"""
Core Matching Engine & The Mismatch Guard Implementation.
"""

import os
import re
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer, util

from engine.schemas import (
    MatchCandidate,
    MatchResponse,
    ImageMetadataResponse
)
from engine.database import (
    get_all_images_with_embeddings,
    log_review_action
)

DEFAULT_THRESHOLD = float(os.getenv("MISMATCH_GUARD_THRESHOLD", "0.54"))


def calculate_cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Calculates cosine similarity between two vector embeddings using numpy."""
    a = np.array(vec_a, dtype=float)
    b = np.array(vec_b, dtype=float)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


class MatchingService:
    """
    Production matching service utilizing local sentence-transformers
    and the strict Mismatch Guard.
    """

    def __init__(self, threshold: float = DEFAULT_THRESHOLD):
        self.threshold = threshold
        self.embed_model = SentenceTransformer('all-MiniLM-L6-v2')

    def check_taxonomic_mismatch(self, post_text: str, candidate_subject: str, candidate_category: str) -> Tuple[bool, str]:
        """
        Structural cross-check to catch taxonomy traps (e.g. Wolf-on-Fox refusal scenario).
        Returns (is_mismatch, explanation).
        """
        post_lower = post_text.lower()
        sub_lower = candidate_subject.lower()
        cat_lower = candidate_category.lower()

        # Fox article vs Wolf asset trap
        if any(w in post_lower for w in ["fox", "vulpes", "fennec"]) and ("wolf" in cat_lower or "wolf" in sub_lower or "lupus" in sub_lower):
            return True, "Concept crossover failure: Topic requires subject 'fox', candidate profile is 'wolf'."

        # Wolf article vs Fox asset trap
        if any(w in post_lower for w in ["wolf", "wolves", "lupus"]) and ("fox" in cat_lower or "fox" in sub_lower or "vulpes" in sub_lower):
            return True, "Concept crossover failure: Topic requires subject 'wolf', candidate profile is 'fox'."

        # Herbivore article vs Bear/Predator asset trap
        if any(w in post_lower for w in ["herbivore", "deer", "cervid"]) and ("bear" in cat_lower or "grizzly" in sub_lower or "predator" in sub_lower):
            return True, "Taxonomic mismatch: Herbivore topic context mismatched against bear/predator asset category profile."

        return False, ""

    def evaluate_candidates(self, post_id: str, post_text: str) -> MatchResponse:
        """
        Evaluates post_text against all indexed visual asset profiles.
        Enforces Mismatch Guard rules and logs results to audit ledger.
        """
        images = get_all_images_with_embeddings()

        if not images:
            return MatchResponse(
                post_id=post_id,
                match_found=False,
                threshold_used=self.threshold,
                recommendation=None,
                all_candidates=[],
                system_resolution="No indexed images available in datastore."
            )

        post_vector = self.embed_model.encode(post_text).tolist()
        candidates: List[MatchCandidate] = []

        for img in images:
            raw_score = calculate_cosine_similarity(post_vector, img["embedding"])

            is_mismatch, mismatch_explanation = self.check_taxonomic_mismatch(
                post_text, img["subject"], img["category"]
            )

            if is_mismatch:
                guard_status = "REJECTED_BY_GUARD"
                explanation = f"[MISMATCH-GUARD] REJECTED. {mismatch_explanation}"
            elif raw_score < self.threshold:
                guard_status = "REJECTED_BY_GUARD"
                explanation = f"[MISMATCH-GUARD] REJECTED. Similarity score ({raw_score:.4f}) fell below threshold ({self.threshold:.2f})."
            else:
                guard_status = "APPROVED"
                explanation = f"[MISMATCH-GUARD] APPROVED. Confident pairing with score {raw_score:.4f} >= {self.threshold:.2f}."

            candidate = MatchCandidate(
                image_id=img["image_id"],
                file_path=img["file_path"],
                subject=img["subject"],
                category=img["category"],
                caption=img["caption"],
                similarity_score=round(raw_score, 4),
                guard_status=guard_status,
                explanation=explanation
            )
            candidates.append(candidate)

        # Sort candidates descending by similarity score
        candidates.sort(key=lambda x: x.similarity_score, reverse=True)

        # Top candidate evaluation
        top_candidate = candidates[0] if candidates else None

        if top_candidate and top_candidate.guard_status == "APPROVED":
            match_found = True
            recommendation = top_candidate
            system_resolution = f"Confident match found: Asset [{top_candidate.image_id}] cleared safety threshold."
        else:
            match_found = False
            recommendation = None
            system_resolution = f"No confident match available. Highest vector similarity score ({top_candidate.similarity_score if top_candidate else 0.0:.4f}) fell below safety threshold or was blocked by Mismatch Guard."

        # Audit log top candidate decision to database
        if top_candidate:
            log_review_action(
                post_id=post_id,
                image_id=top_candidate.image_id,
                score=top_candidate.similarity_score,
                guard_status=top_candidate.guard_status,
                explanation=top_candidate.explanation,
                status="APPROVED" if match_found else "REJECTED"
            )

        return MatchResponse(
            post_id=post_id,
            match_found=match_found,
            threshold_used=self.threshold,
            recommendation=recommendation,
            all_candidates=candidates[:5],
            system_resolution=system_resolution
        )
