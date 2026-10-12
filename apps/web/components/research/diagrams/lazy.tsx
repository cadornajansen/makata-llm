"use client"

import dynamic from "next/dynamic"

// The server article loader knows every article. This client boundary keeps each
// topic's interactive code in a separate chunk while retaining default SSR.
export const VectorExplorer = dynamic(() =>
  import("./mathematics").then((module) => module.VectorExplorer)
)
export const MatrixExplorer = dynamic(() =>
  import("./mathematics").then((module) => module.MatrixExplorer)
)
export const GradientDescent = dynamic(() =>
  import("./mathematics").then((module) => module.GradientDescent)
)
export const ChainRule = dynamic(() =>
  import("./mathematics").then((module) => module.ChainRule)
)
export const NetworkExplorer = dynamic(() =>
  import("./neural-networks").then((module) => module.NetworkExplorer)
)
export const ActivationExplorer = dynamic(() =>
  import("./neural-networks").then((module) => module.ActivationExplorer)
)
export const AutogradExplorer = dynamic(() =>
  import("./pytorch").then((module) => module.AutogradExplorer)
)
export const TrainingExplorer = dynamic(() =>
  import("./pytorch").then((module) => module.TrainingExplorer)
)
export const TokenizationExplorer = dynamic(() =>
  import("./transformers").then((module) => module.TokenizationExplorer)
)
export const AttentionExplorer = dynamic(() =>
  import("./transformers").then((module) => module.AttentionExplorer)
)
export const TransformerExplorer = dynamic(() =>
  import("./transformers").then((module) => module.TransformerExplorer)
)
export const SamplingExplorer = dynamic(() =>
  import("./transformers").then((module) => module.SamplingExplorer)
)
export const ParameterExplorer = dynamic(() =>
  import("./llm-training").then((module) => module.ParameterExplorer)
)
export const LoraExplorer = dynamic(() =>
  import("./llm-training").then((module) => module.LoraExplorer)
)
export const DistillationExplorer = dynamic(() =>
  import("./llm-training").then((module) => module.DistillationExplorer)
)
export const CleaningPipeline = dynamic(() =>
  import("./dataset-engineering").then((module) => module.CleaningPipeline)
)
export const DatasetSplitExplorer = dynamic(() =>
  import("./dataset-engineering").then((module) => module.DatasetSplitExplorer)
)
export const TokenizationComparison = dynamic(() =>
  import("./dataset-engineering").then(
    (module) => module.TokenizationComparison
  )
)
export const ContaminationExplorer = dynamic(() =>
  import("./dataset-engineering").then((module) => module.ContaminationExplorer)
)
export const ConfusionMatrixExplorer = dynamic(() =>
  import("./evaluation").then((module) => module.ConfusionMatrixExplorer)
)
export const EvaluationExplorer = dynamic(() =>
  import("./evaluation").then((module) => module.EvaluationExplorer)
)
export const ParallelismExplorer = dynamic(() =>
  import("./gpu-computing").then((module) => module.ParallelismExplorer)
)
export const MemoryExplorer = dynamic(() =>
  import("./gpu-computing").then((module) => module.MemoryExplorer)
)
export const BatchExplorer = dynamic(() =>
  import("./gpu-computing").then((module) => module.BatchExplorer)
)
export const CheckpointExplorer = dynamic(() =>
  import("./gpu-computing").then((module) => module.CheckpointExplorer)
)
