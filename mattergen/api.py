# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

PRETRAINED_MODEL_NAME = Literal[
    "mattergen_base",
    "chemical_system",
    "space_group",
    "dft_mag_density",
    "dft_band_gap",
    "ml_bulk_modulus",
    "dft_mag_density_hhi_score",
    "chemical_system_energy_above_hull",
    "mp_20_base",
]


def _resolve_local_checkpoint_dir(model_name: PRETRAINED_MODEL_NAME) -> Path:
    root = Path(__file__).resolve().parent.parent
    checkpoint_dir = root / "checkpoints" / model_name
    if not checkpoint_dir.exists():
        raise FileNotFoundError(
            f"Local checkpoint directory not found: {checkpoint_dir}. "
            "Pull it first via: git lfs pull -I checkpoints/ --exclude=\"\""
        )
    return checkpoint_dir


def generate_materials(
    output_path: str | Path,
    pretrained_name: PRETRAINED_MODEL_NAME = "mattergen_base",
    batch_size: int = 1,
    num_batches: int = 1,
    properties_to_condition_on: dict[str, Any] | None = None,
    record_trajectories: bool = False,
    diffusion_guidance_factor: float = 0.0,
    use_local_checkpoints: bool = False,
) -> list[Any]:
    """Generate crystal structures from a pretrained MatterGen checkpoint.

    Args:
        output_path: Directory where generated files are saved.
        pretrained_name: Name of a supported pretrained MatterGen model.
        batch_size: Number of samples per diffusion batch.
        num_batches: Number of diffusion batches to run.
        properties_to_condition_on: Optional property values for conditional generation.
        record_trajectories: If True, also writes denoising trajectories.
        diffusion_guidance_factor: Classifier-free guidance factor.
        use_local_checkpoints: If True, load checkpoints from local `checkpoints/`.

    Returns:
        A list of generated pymatgen Structure objects.
    """
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Import heavy model dependencies only when generation is requested.
    from mattergen.common.utils.data_classes import MatterGenCheckpointInfo
    from mattergen.generator import CrystalGenerator

    if use_local_checkpoints:
        checkpoint_info = MatterGenCheckpointInfo(
            model_path=_resolve_local_checkpoint_dir(pretrained_name),
            load_epoch="last",
            config_overrides=[],
            strict_checkpoint_loading=True,
        )
    else:
        checkpoint_info = MatterGenCheckpointInfo.from_hf_hub(
            pretrained_name,
            config_overrides=[],
        )

    generator = CrystalGenerator(
        checkpoint_info=checkpoint_info,
        batch_size=batch_size,
        num_batches=num_batches,
        properties_to_condition_on=properties_to_condition_on or {},
        record_trajectories=record_trajectories,
        diffusion_guidance_factor=diffusion_guidance_factor,
    )
    return generator.generate(output_dir=output_dir)


def generate_with_model_path(
    output_path: str | Path,
    model_path: str | Path,
    batch_size: int = 1,
    num_batches: int = 1,
    properties_to_condition_on: dict[str, Any] | None = None,
    record_trajectories: bool = False,
    diffusion_guidance_factor: float = 0.0,
    config_overrides: list[str] | None = None,
) -> list[Any]:
    """Generate crystal structures from a custom local model checkpoint directory."""
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Import heavy model dependencies only when generation is requested.
    from mattergen.common.utils.data_classes import MatterGenCheckpointInfo
    from mattergen.generator import CrystalGenerator

    checkpoint_info = MatterGenCheckpointInfo(
        model_path=Path(model_path).resolve(),
        load_epoch="last",
        config_overrides=config_overrides or [],
        strict_checkpoint_loading=True,
    )
    generator = CrystalGenerator(
        checkpoint_info=checkpoint_info,
        batch_size=batch_size,
        num_batches=num_batches,
        properties_to_condition_on=properties_to_condition_on or {},
        record_trajectories=record_trajectories,
        diffusion_guidance_factor=diffusion_guidance_factor,
    )
    return generator.generate(output_dir=output_dir)


def generation_defaults() -> dict[str, Any]:
    """Return a small defaults dictionary for calling code."""
    return {
        "pretrained_name": "mattergen_base",
        "batch_size": 1,
        "num_batches": 1,
        "record_trajectories": False,
        "diffusion_guidance_factor": 0.0,
        "use_local_checkpoints": False,
    }
