"""CPU-only educational regression example; not a Makata language-model experiment."""

from __future__ import annotations

import argparse
import copy
import json
import platform
from pathlib import Path
from typing import Any

import torch
from torch import Tensor, nn
from torch.utils.data import DataLoader, TensorDataset, random_split


class Regressor(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.linear = nn.Linear(2, 1)

    def forward(self, inputs: Tensor) -> Tensor:
        return self.linear(inputs)


def make_data() -> tuple[TensorDataset, TensorDataset, TensorDataset]:
    generator = torch.Generator().manual_seed(41)
    inputs = torch.randn(512, 2, generator=generator)
    noise = 0.1 * torch.randn(512, 1, generator=generator)
    targets = inputs @ torch.tensor([[3.0], [-2.0]]) + 0.5 + noise
    dataset = TensorDataset(inputs, targets)
    partitions = random_split(
        dataset, [384, 64, 64], generator=torch.Generator().manual_seed(42)
    )
    return tuple(
        TensorDataset(inputs[part.indices], targets[part.indices])
        for part in partitions
    )


def train_epoch(
    model: Regressor,
    loader: DataLoader[tuple[Tensor, ...]],
    optimizer: torch.optim.Optimizer,
) -> float:
    model.train()
    loss_fn = nn.MSELoss()
    squared_error = 0.0
    count = 0
    for inputs, targets in loader:
        optimizer.zero_grad(set_to_none=True)
        predictions = model(inputs)
        if predictions.shape != targets.shape:
            raise ValueError("Prediction and target shapes must match.")
        loss = loss_fn(predictions, targets)
        if not torch.isfinite(loss):
            raise RuntimeError("Non-finite training loss.")
        loss.backward()
        optimizer.step()
        squared_error += loss.item() * targets.numel()
        count += targets.numel()
    return squared_error / count


@torch.no_grad()
def evaluate(model: Regressor, loader: DataLoader[tuple[Tensor, ...]]) -> float:
    model.eval()
    squared_error = 0.0
    count = 0
    for inputs, targets in loader:
        predictions = model(inputs)
        squared_error += (predictions - targets).square().sum().item()
        count += targets.numel()
    return squared_error / count


def run(epochs: int, output: Path, resume: Path | None) -> dict[str, Any]:
    if epochs < 1:
        raise ValueError("Epochs must be positive.")
    torch.manual_seed(7)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    training, validation, testing = make_data()
    loader_generator = torch.Generator().manual_seed(43)
    training_loader = DataLoader(
        training, batch_size=32, shuffle=True, generator=loader_generator,
        num_workers=0,
    )
    validation_loader = DataLoader(validation, batch_size=64, num_workers=0)
    test_loader = DataLoader(testing, batch_size=64, num_workers=0)
    model = Regressor()
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.03, weight_decay=0.0)
    start_epoch = 0
    best_validation = float("inf")
    best_state = copy.deepcopy(model.state_dict())
    history: list[dict[str, float | int]] = []

    if resume is not None:
        checkpoint = torch.load(resume, map_location="cpu", weights_only=True)
        model.load_state_dict(checkpoint["model"])
        optimizer.load_state_dict(checkpoint["optimizer"])
        start_epoch = checkpoint["epoch"]
        best_validation = checkpoint["best_validation"]
        best_state = checkpoint["best_model"]
        history = checkpoint["history"]
        loader_generator.set_state(checkpoint["loader_rng"])
        torch.set_rng_state(checkpoint["torch_rng"])
        if epochs <= start_epoch:
            raise ValueError("--epochs must exceed the checkpoint's epoch.")

    output.mkdir(parents=True, exist_ok=True)
    initial_validation = evaluate(model, validation_loader)
    for epoch in range(start_epoch, epochs):
        training_loss = train_epoch(model, training_loader, optimizer)
        validation_loss = evaluate(model, validation_loader)
        history.append(
            {"epoch": epoch + 1, "train_mse": training_loss, "val_mse": validation_loss}
        )
        if validation_loss < best_validation:
            best_validation = validation_loss
            best_state = copy.deepcopy(model.state_dict())
        # Save after an epoch, when no partially consumed sampler needs restoring.
        torch.save(
            {
                "epoch": epoch + 1,
                "model": model.state_dict(),
                "optimizer": optimizer.state_dict(),
                "best_validation": best_validation,
                "best_model": best_state,
                "history": history,
                "loader_rng": loader_generator.get_state(),
                "torch_rng": torch.get_rng_state(),
                "torch_version": str(torch.__version__),
                "python_version": platform.python_version(),
            },
            output / "last.pt",
        )

    checkpoint = torch.load(output / "last.pt", map_location="cpu", weights_only=True)
    restored = Regressor()
    restored.load_state_dict(checkpoint["model"])
    model.eval()
    restored.eval()
    with torch.no_grad():
        probe = validation.tensors[0]
        torch.testing.assert_close(model(probe), restored(probe), rtol=0, atol=0)

    model.load_state_dict(best_state)
    torch.save(best_state, output / "best-weights.pt")
    result = {
        "educational_example": True,
        "python_version": platform.python_version(),
        "torch_version": str(torch.__version__),
        "device": "cpu",
        "epochs": epochs,
        "initial_validation_mse": initial_validation,
        "best_validation_mse": best_validation,
        "test_mse": evaluate(model, test_loader),
        "weights": model.linear.weight.detach().tolist(),
        "bias": model.linear.bias.detach().tolist(),
        "checkpoint_roundtrip_exact": True,
    }
    (output / "history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    (output / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=80, help="Total epochs, including resumed epochs.")
    parser.add_argument("--output", type=Path, default=Path("regression-output"))
    parser.add_argument("--resume", type=Path, default=None)
    arguments = parser.parse_args()
    result = run(arguments.epochs, arguments.output, arguments.resume)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
