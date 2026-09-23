export interface PortfolioProject {
  id: string;
  name: string;
  route: string;
  title: RegExp;
  description: RegExp;
  requiredSections: RegExp[];
  githubHref: string;
}

export const portfolioProjects: PortfolioProject[] = [
  {
    id: 'customer-churn',
    name: 'Customer Churn',
    route: '#/projects/customer-churn',
    title: /intelligent customer churn prediction/i,
    description: /traditional ml.*production api/i,
    requiredSections: [/problem/i, /architecture/i, /api \/ application/i],
    githubHref: 'https://github.com/KN-Vignesh/intelligent-customer-churn-prediction',
  },
  {
    id: 'lora',
    name: 'LoRA / Qwen',
    route: '#/Ai-Cookbook/LoraFine-tuning/README',
    title: /qwen \/ lora\s*adaptation/i,
    description: /open-weight language model.*retraining the entire model/i,
    requiredSections: [/the problem/i, /system(?!s)/i, /implementation/i],
    githubHref: 'https://github.com/KN-Vignesh/Projects/tree/main/Ai-Cookbook/LoraFine-tuning',
  },
  {
    id: 'qlora',
    name: 'QLoRA',
    route: '#/Ai-Cookbook/QLoraFine-Tuning/README',
    title: /^qlora$/i,
    description: /large-language-model adaptation.*memory is constrained/i,
    requiredSections: [/the problem/i, /the approach/i, /the system/i],
    githubHref: 'https://github.com/KN-Vignesh/Projects/tree/main/Ai-Cookbook/QLoraFine-Tuning',
  },
  {
    id: 'bert',
    name: 'BERT',
    route: '#/Ai-Cookbook/BERT_MODEL/README',
    title: /^bert$/i,
    description: /adapting pretrained transformer models/i,
    requiredSections: [/the problem/i, /the approach/i, /the system/i],
    githubHref: 'https://github.com/KN-Vignesh/Projects/tree/main/Ai-Cookbook/BERT_MODEL',
  },
  {
    id: 'evaluation',
    name: 'Model Evaluation',
    route: '#/Ai-Cookbook/Combined_metric_Calc/README',
    title: /model evaluation/i,
    description: /combining metrics across experiments/i,
    requiredSections: [/the problem/i, /the approach/i, /the system/i],
    githubHref: 'https://github.com/KN-Vignesh/Projects/tree/main/Ai-Cookbook/Combined_metric_Calc',
  },
  {
    id: 'cnn',
    name: 'CNN Fundamentals',
    route: '#/Ai-Cookbook/CNN-Fundamentals/README',
    title: /cnn fundamentals/i,
    description: /raw images to learned visual features/i,
    requiredSections: [/the problem/i, /the approach/i, /the system/i],
    githubHref: 'https://github.com/KN-Vignesh/Projects/tree/main/Ai-Cookbook/CNN-Fundamentals',
  },
  {
    id: 'house-price',
    name: 'House Price Prediction',
    route: '#/Data-recipe/House_Price_Prediction/README',
    title: /house price prediction/i,
    description: /structured machine-learning workflow/i,
    requiredSections: [/the problem/i, /the approach/i, /the system/i],
    githubHref: 'https://github.com/KN-Vignesh/Projects/tree/main/Data-recipe/House_Price_Prediction',
  },
  {
    id: 'titanic',
    name: 'Titanic',
    route: '#/Data-recipe/Titanic_Model/README',
    title: /^titanic$/i,
    description: /foundational supervised-learning workflow/i,
    requiredSections: [/the problem/i, /the approach/i, /the system/i],
    githubHref: 'https://github.com/KN-Vignesh/Projects/tree/main/Data-recipe/Titanic_Model',
  },
  {
    id: 'vero',
    name: 'VERO',
    route: '#/docs/VERO/README',
    title: /^vero$/i,
    description: /ai code analysis for pull requests/i,
    requiredSections: [/what it does/i, /documentation/i, /configuration/i],
    githubHref: 'https://github.com/KN-Vignesh/Projects',
  },
];