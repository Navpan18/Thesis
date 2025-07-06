import torch
import torch.nn as nn
from torchvision import models


class _GR(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x, lambda_):
        ctx.lambda_ = lambda_
        return x.view_as(x)

    @staticmethod
    def backward(ctx, grad_output):
        return grad_output.neg() * ctx.lambda_, None


class GRL(nn.Module):
    def __init__(self, lambda_=0.0):
        super().__init__()
        self.lambda_ = lambda_

    def forward(self, x):
        return _GR.apply(x, self.lambda_)


class DANNModel(nn.Module):
    def __init__(
        self, num_disease, num_species, lambda_init=0.0, plant_head_type="linear"
    ):
        super().__init__()
        self.encoder = models.resnet50(weights=None)
        self.encoder.fc = nn.Identity()
        self.cls_head = nn.Linear(2048, num_disease)
        self.grl = GRL(lambda_init)
        if plant_head_type == "linear":
            self.plant_head = nn.Linear(2048, num_species)
        else:
            self.plant_head = nn.Sequential(
                nn.Linear(2048, 128),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(128, num_species),
            )

    def forward(self, x):
        f = self.encoder(x)
        y_disease = self.cls_head(f)
        y_species = self.plant_head(self.grl(f))
        return y_disease, y_species
