"""ai_core/utils/agronomy.py"""

from schemas.ai_models import CropStage

PADDY_STAGE_THRESHOLDS: tuple[tuple[int, CropStage], ...] = (
    (20, CropStage.SEEDLING),
    (45, CropStage.TILLERING),
    (65, CropStage.PANICLE_INITIATION),
    (80, CropStage.BOOTING),
    (90, CropStage.HEADING),
    (100, CropStage.FLOWERING),
    (115, CropStage.MILKY),
)


def calculate_paddy_stage(age_days: int | None) -> CropStage | None:
    """Derives growth stage by iterating over declarative day boundaries."""
    if age_days is None or age_days < 0:
        return None

    for max_days, stage in PADDY_STAGE_THRESHOLDS:
        if age_days <= max_days:
            return stage

    return CropStage.MATURITY
