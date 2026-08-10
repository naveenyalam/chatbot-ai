"use client";

import React, { useState } from "react";
import { FileCode2, Sparkles, X, ArrowRight } from "lucide-react";
import { useToast } from "@/components/ui/Toast";

interface TemplateItem {
  id: string;
  title: string;
  category: string;
  description: string;
  template: string;
  variables: { name: string; label: string; placeholder: string }[];
}

interface ChatTemplatesProps {
  onInsertTemplate?: (filledContent: string) => void;
}

export function ChatTemplates({ onInsertTemplate }: ChatTemplatesProps) {
  const toast = useToast();
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateItem | null>(null);
  const [varValues, setVarValues] = useState<Record<string, string>>({});

  const templates: TemplateItem[] = [
    {
      id: "explain-topic",
      title: "Explain Complex Topic",
      category: "Study & Learning",
      description: "Break down intricate technical or academic concepts with analogies.",
      template: "Explain {{topic}} at a {{level}} level. Include intuitive analogies, 3 key principles, and real-world applications.",
      variables: [
        { name: "topic", label: "Topic / Subject", placeholder: "Quantum computing, Neural Networks..." },
        { name: "level", label: "Target Audience Level", placeholder: "beginner, high school, senior engineer..." }
      ]
    },
    {
      id: "executive-summary",
      title: "Executive Summary Generator",
      category: "Writing",
      description: "Create a concise, impact-focused executive summary for leadership review.",
      template: "Draft a concise {{length}} executive summary for {{project_name}}.\n\nContext & Raw Notes:\n{{context}}\n\nHighlight top 3 strategic priorities, ROI impact, and key deadlines.",
      variables: [
        { name: "length", label: "Desired Length", placeholder: "1-paragraph, 1-page bulleted..." },
        { name: "project_name", label: "Project / Proposal Name", placeholder: "NOVA Platform OS Migration..." },
        { name: "context", label: "Background / Key Context", placeholder: "Migrating backend services to async FastAPI..." }
      ]
    },
    {
      id: "code-review",
      title: "Comprehensive Code Review",
      category: "Coding",
      description: "Perform structured code review covering performance, security, and cleanliness.",
      template: "Conduct a thorough code review for the following {{language}} code snippet focusing on {{focus}}:\n\nKey Concerns:\n- Performance & Complexity\n- Security Vulnerabilities\n- Architectural Best Practices",
      variables: [
        { name: "language", label: "Language / Stack", placeholder: "TypeScript, Python, Go..." },
        { name: "focus", label: "Primary Focus Area", placeholder: "Security audit, performance, error handling..." }
      ]
    },
    {
      id: "data-analysis",
      title: "Dataset Insights & Summary",
      category: "Data Analysis",
      description: "Generate structured analytical takeaways and business insights from data.",
      template: "Analyze the dataset described below to answer: {{business_question}}\n\nDataset Summary:\n{{dataset_info}}\n\nOutput format: Key Metrics, Anomalies, Actionable Business Recommendations.",
      variables: [
        { name: "business_question", label: "Business Question", placeholder: "Which customer tier has highest churn risk?" },
        { name: "dataset_info", label: "Dataset Description / Sample Data", placeholder: "CSV containing columns user_id, MRR, last_login_date..." }
      ]
    },
    {
      id: "research-report",
      title: "Deep Research Report",
      category: "Research",
      description: "Synthesize multi-source research into a structured markdown report.",
      template: "Conduct a comprehensive research report on {{topic}}.\n\nDepth: {{depth}}\nFormat: Abstract, Core Analysis, Market Comparison, Future Outlook, Conclusion.",
      variables: [
        { name: "topic", label: "Research Topic", placeholder: "Solid-state battery commercialization 2026..." },
        { name: "depth", label: "Research Depth", placeholder: "Executive overview, Deep technical breakdown..." }
      ]
    },
    {
      id: "resume-improvement",
      title: "Resume & Portfolio Polish",
      category: "Career",
      description: "Refactor bullet points using Action Verb + Task + Quantified Impact framework.",
      template: "Target Role: {{target_role}}\n\nRefactor the following experience bullet points using the Google XYZ formula (Accomplished [X] as measured by [Y], by doing [Z]):\n\nCurrent Bullets:\n{{bullets}}",
      variables: [
        { name: "target_role", label: "Target Role", placeholder: "Staff AI Architect, Staff Engineer..." },
        { name: "bullets", label: "Current Experience Text", placeholder: "Built database service that improved speed..." }
      ]
    }
  ];

  const handleOpenTemplate = (t: TemplateItem) => {
    setSelectedTemplate(t);
    const initialVals: Record<string, string> = {};
    t.variables.forEach((v) => { initialVals[v.name] = ""; });
    setVarValues(initialVals);
  };

  const handleApplyTemplate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTemplate) return;

    let filled = selectedTemplate.template;
    selectedTemplate.variables.forEach((v) => {
      const val = varValues[v.name] || `[${v.label}]`;
      filled = filled.replaceAll(`{{${v.name}}}`, val);
    });

    onInsertTemplate?.(filled);
    toast.success(`Applied template "${selectedTemplate.title}".`);
    setSelectedTemplate(null);
  };

  return (
    <div className="flex-1 p-6 md:p-8 max-w-6xl mx-auto w-full space-y-6 overflow-y-auto">
      <div className="border-b border-border pb-5 flex items-center gap-2.5">
        <div className="p-2 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400">
          <FileCode2 className="w-5 h-5" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-foreground">Interactive Chat Templates</h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Select a structured template, customize variable parameters, and inject directly into conversation.
          </p>
        </div>
      </div>

      {/* Grid of Templates */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {templates.map((t) => (
          <div key={t.id} className="p-5 rounded-2xl bg-surface border border-border hover:border-blue-500/30 transition-all glass-panel flex flex-col justify-between space-y-3 group">
            <div>
              <span className="px-2.5 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 text-[10px] font-bold uppercase tracking-wider">
                {t.category}
              </span>
              <h3 className="text-sm font-bold text-foreground mt-2 group-hover:text-blue-400 transition-colors">{t.title}</h3>
              <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{t.description}</p>
            </div>
            <button
              onClick={() => handleOpenTemplate(t)}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-surface hover:bg-surface-hover border border-border text-xs font-semibold text-foreground transition-all cursor-pointer"
            >
              <Sparkles className="w-3.5 h-3.5 text-blue-400" />
              <span>Use Template</span>
            </button>
          </div>
        ))}
      </div>

      {/* Variable Substitution Modal */}
      {selectedTemplate && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <form onSubmit={handleApplyTemplate} className="w-full max-w-lg p-6 rounded-2xl bg-surface-elevated border border-border glass-panel shadow-2xl space-y-4 animate-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <h3 className="text-sm font-bold text-foreground">{selectedTemplate.title}</h3>
              <button type="button" onClick={() => setSelectedTemplate(null)} className="p-1 rounded-lg text-muted-foreground hover:text-foreground">
                <X className="w-4 h-4" />
              </button>
            </div>
            <p className="text-xs text-muted-foreground">Fill in the fields below to customize your prompt:</p>
            <div className="space-y-3">
              {selectedTemplate.variables.map((v) => (
                <div key={v.name} className="space-y-1">
                  <label className="text-xs font-semibold text-foreground">{v.label}</label>
                  <input
                    type="text"
                    placeholder={v.placeholder}
                    value={varValues[v.name] || ""}
                    onChange={(e) => setVarValues({ ...varValues, [v.name]: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-surface border border-border text-xs text-foreground focus:outline-none focus:border-blue-500"
                  />
                </div>
              ))}
            </div>
            <div className="flex justify-end gap-2 pt-2 border-t border-border">
              <button
                type="button"
                onClick={() => setSelectedTemplate(null)}
                className="px-4 py-2 rounded-xl border border-border hover:bg-surface-hover text-xs font-semibold text-foreground"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md flex items-center gap-1.5 cursor-pointer"
              >
                <span>Inject into Chat</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
