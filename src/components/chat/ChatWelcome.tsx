"use client";

import React from "react";
import { Code, BookOpen, PenTool, BarChart3, Search, FileText, Bot, Sparkles, Lightbulb, CheckSquare, FileSearch } from "lucide-react";
import { GlowOrb } from "../ui/GlowOrb";
import { SuggestionCard } from "./SuggestionCard";
import { WorkspaceView } from "@/types";

interface ChatWelcomeProps {
  onSelectPrompt: (prompt: string) => void;
  activeView?: WorkspaceView;
}

export function ChatWelcome({ onSelectPrompt, activeView = "chat" }: ChatWelcomeProps) {
  const getSuggestions = () => {
    switch (activeView) {
      case "research":
        return [
          {
            title: "Research Topic",
            description: "Deep multi-source synthesis on a research query",
            prompt: "Research quantum computing applications in healthcare and present a structured summary.",
            icon: Search,
          },
          {
            title: "Compare Technologies",
            description: "Synthesize tradeoffs between frameworks",
            prompt: "Compare PostgreSQL with vector extensions versus dedicated vector databases like Qdrant and Milvus.",
            icon: BookOpen,
          },
          {
            title: "Market Analysis",
            description: "Structure findings for executive review",
            prompt: "Analyze current market trends in generative AI autonomous workforce tools for enterprise.",
            icon: BarChart3,
          },
          {
            title: "Literature Review",
            description: "Summarize academic and technical literature",
            prompt: "Synthesize key breakthroughs in LLM context window expansion techniques over the past 2 years.",
            icon: FileSearch,
          },
        ];

      case "writing":
        return [
          {
            title: "Draft Executive Summary",
            description: "Create a polished executive overview",
            prompt: "Draft a 1-page executive summary for a project launch proposal focusing on security, scale, and ROI.",
            icon: PenTool,
          },
          {
            title: "Rewrite & Polish",
            description: "Improve clarity, flow, and tone",
            prompt: "Rewrite the following text into a compelling, professional, and clear enterprise communication tone: ",
            icon: Sparkles,
          },
          {
            title: "Technical Documentation",
            description: "Generate comprehensive API or system docs",
            prompt: "Draft clear developer documentation for an asynchronous REST API streaming endpoint.",
            icon: FileText,
          },
          {
            title: "Email & Proposal",
            description: "Compose persuasive business correspondence",
            prompt: "Compose a high-converting client update email highlighting completed milestone features and next steps.",
            icon: Lightbulb,
          },
        ];

      case "code":
        return [
          {
            title: "Explain & Debug",
            description: "Analyze code logic, root cause, and fixes",
            prompt: "Explain how to debug memory leaks in Node.js event listeners and provide refactored code.",
            icon: Code,
          },
          {
            title: "Generate Unit Tests",
            description: "Create comprehensive test suites",
            prompt: "Write PyTest unit test cases with mocks for a FastAPI async database service method.",
            icon: CheckSquare,
          },
          {
            title: "Refactor for Speed",
            description: "Optimize execution time and clean up syntax",
            prompt: "Refactor this Python algorithm to improve time complexity from O(n^2) to O(n log n).",
            icon: Sparkles,
          },
          {
            title: "Build Feature Component",
            description: "Create production ready UI or API code",
            prompt: "Build a TypeScript custom hook for handling infinite scroll with virtualized lists in React.",
            icon: Code,
          },
        ];

      case "data":
        return [
          {
            title: "Analyze Dataset",
            description: "Find patterns, trends, and statistics",
            prompt: "Help me analyze a dataset with customer transaction history to find top purchasing segments.",
            icon: BarChart3,
          },
          {
            title: "Summary Metrics",
            description: "Calculate KPIs and distributions",
            prompt: "Explain how to calculate monthly churn rate, LTV, and CAC from raw subscription log data.",
            icon: Lightbulb,
          },
          {
            title: "Data Cleaning Script",
            description: "Write Python pandas or SQL cleaning scripts",
            prompt: "Write a Python script using pandas to handle missing values, normalize timestamps, and deduplicate rows.",
            icon: Code,
          },
          {
            title: "SQL Query Optimization",
            description: "Write high-performance relational queries",
            prompt: "Write an optimized SQL window function query to rank top 5 products per region for each quarter.",
            icon: FileText,
          },
        ];

      case "documents":
        return [
          {
            title: "Ask Document Question",
            description: "Extract grounded facts from uploaded RAG files",
            prompt: "Ask NOVA to analyze my uploaded documents and list all key contractual obligations.",
            icon: FileText,
          },
          {
            title: "Summarize Knowledge Base",
            description: "Synthesize main themes across documents",
            prompt: "Synthesize the main conclusions and key takeaways across all uploaded PDF documents.",
            icon: BookOpen,
          },
          {
            title: "Find Specific Clauses",
            description: "Locate specific terms or requirements",
            prompt: "Search my indexed knowledge base for references to SLA guarantees and data retention rules.",
            icon: FileSearch,
          },
          {
            title: "Extract Structured Data",
            description: "Convert document text into JSON/CSV",
            prompt: "Extract table data and key metrics from the uploaded report into a structured JSON schema.",
            icon: BarChart3,
          },
        ];

      case "agents":
        return [
          {
            title: "Delegate Multi-Step Task",
            description: "Execute complex task with autonomous agent",
            prompt: "Task Agent: Break down the process of auditing API security into 4 steps and execute step 1.",
            icon: Bot,
          },
          {
            title: "Document Synthesis Agent",
            description: "Deep RAG analysis across multiple files",
            prompt: "Document Agent: Analyze all indexed documents for compliance gaps and report actionable fixes.",
            icon: FileText,
          },
          {
            title: "Deep Research Agent",
            description: "Structured multi-stage research pipeline",
            prompt: "Research Agent: Conduct deep research on zero-trust cloud architecture standards for enterprise.",
            icon: Search,
          },
          {
            title: "Code Execution Task",
            description: "Run sandboxed code analysis tasks",
            prompt: "Task Agent: Write Python code to calculate Fibonacci primes up to 1000 and verify output.",
            icon: Code,
          },
        ];

      default:
        return [
          {
            title: "Build & Architecture",
            description: "Outline system architecture and designs",
            prompt: "I want to build a scalable Next.js and FastAPI application. Help me outline the component architecture.",
            icon: Code,
          },
          {
            title: "Explain & Reason",
            description: "Explain complex concepts step by step",
            prompt: "Explain quantum computing and multi-head attention mechanisms in clear, accessible terms.",
            icon: BookOpen,
          },
          {
            title: "Draft & Rewrite",
            description: "Write polished content from scratch",
            prompt: "Draft a clear, engaging project announcement email detailing new platform capabilities.",
            icon: PenTool,
          },
          {
            title: "Analyze & Synthesize",
            description: "Evaluate trade-offs or analyze ideas",
            prompt: "Analyze the pros and cons of event-driven architectures versus synchronous microservices.",
            icon: BarChart3,
          },
        ];
    }
  };

  const suggestions = getSuggestions();
  const getWorkspaceBadgeText = () => {
    switch (activeView) {
      case "research": return "Research Mode Workspace";
      case "writing": return "Writing Assistant Mode";
      case "code": return "Developer Sandbox";
      case "data": return "Data Analysis Workspace";
      case "documents": return "Knowledge RAG Base";
      case "agents": return "Autonomous Agent Workspace";
      default: return "Your Intelligent AI Workspace";
    }
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center py-8 px-4 max-w-4xl mx-auto overflow-y-auto w-full select-none">
      {/* AI Orb */}
      <div className="mb-6 flex justify-center">
        <GlowOrb />
      </div>

      {/* Hero Headings */}
      <div className="text-center space-y-2 mb-10 max-w-2xl">
        <span className="text-[10px] font-extrabold tracking-widest text-accent dark:text-accent uppercase bg-accent/5 dark:bg-accent/10 px-3 py-1 rounded-full border border-accent/10">
          {getWorkspaceBadgeText()}
        </span>
        <h2 className="text-3xl md:text-4xl font-extrabold tracking-tight text-text-primary bg-clip-text mt-3">
          What will we create today?
        </h2>
        <p className="text-sm text-text-muted max-w-lg mx-auto">
          Ask, explore, research, code, or turn ideas into intelligent results.
        </p>
      </div>

      {/* Suggestions Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full px-2 sm:px-4">
        {suggestions.map((card, index) => (
          <SuggestionCard
            key={index}
            title={card.title}
            description={card.description}
            prompt={card.prompt}
            icon={card.icon}
            onClick={onSelectPrompt}
          />
        ))}
      </div>
    </div>
  );
}

