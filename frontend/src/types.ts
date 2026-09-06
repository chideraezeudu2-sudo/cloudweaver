export interface FAQItem {
  id: string;
  question: string;
  answer: string;
}

export interface PricingOption {
  amount: number;
  label: string;
  popular?: boolean;
  estHours4090: string;
  estHoursA100: string;
}

export interface VerificationStep {
  number: string;
  title: string;
  description: string;
  technicalDetail: string;
}

export interface InstallStep {
  number: number;
  command: string;
  title: string;
  description: string;
}
