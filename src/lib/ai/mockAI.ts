import { Message } from "@/types";
import { StreamOptions, StreamController } from "./types";

// Database of rich mock responses supporting headings, lists, tables, code, quotes, rules
const MOCK_RESPONSES = {
  default: `Hello! I am **Nova**, your premium AI workspace assistant. I can help you design software systems, write or inspect code, draft content, or analyze complex data sets.

Here is a summary of what I can do:
1. **Develop Projects**: Scaffold architectural structures for Next.js, React, Python, or Go.
2. **Explain Concepts**: Simplify advanced logic like quantum computation or vector index layouts.
3. **Refactor Code**: Write clean, optimized, and type-safe functions.

### Quick Example Table
| Capabilities | Description | Speed |
| :--- | :--- | :--- |
| **Code Generation** | Full scaffolding with syntactical details | Fast |
| **System Research** | Multi-vector analysis on topics | Detailed |
| **Logic Tuning** | Debugging and optimization routines | Instant |

Let me know how we should begin!`,

  code: `Here is a complete, type-safe API route structure for handling session tokens in Next.js using the App Router.

### File: \`src/app/api/session/route.ts\`
\`\`\`typescript
import { NextRequest, NextResponse } from "next/server";

interface SessionPayload {
  userId: string;
  expiresIn: number;
}

export async function POST(req: NextRequest) {
  try {
    const body: SessionPayload = await req.json();
    
    if (!body.userId) {
      return NextResponse.json(
        { error: "Missing userId parameter" },
        { status: 400 }
      );
    }

    const sessionToken = crypto.randomUUID();
    
    return NextResponse.json({
      token: sessionToken,
      status: "authenticated",
      expires: Date.now() + body.expiresIn * 1000,
    });
  } catch (err) {
    return NextResponse.json(
      { error: "Internal server validation failure" },
      { status: 500 }
    );
  }
}
\`\`\`

> [!NOTE]
> Ensure you import \`NextResponse\` and validate incoming payload sizes on edge functions to avoid Denial-of-Service constraints.`,

  quantum: `Quantum computing shifts standard binary execution into quantum probability fields. Instead of representing bits as definite \`0\`s or \`1\`s, it operates on three pillars:

### 1. Superposition
A **qubit** (quantum bit) can represent a state of both \`0\` and \`1\` at the same time. This is represented mathematically by a linear combination of states:
$$ |\\psi\\rangle = \\alpha|0\\rangle + \\beta|1\\rangle $$

### 2. Entanglement
Qubits link together in pairs or groups. Changing the spin of one qubit immediately defines the spin of its entangled partner:
* **Entangled Pair A**: Spin-Up (0)
* **Entangled Pair B**: Spin-Down (1)

### 3. Interference
Quantum systems use interference to amplify pathways leading to the correct answers while canceling out incorrect outcomes.

---

### Comparison of Processing
| Parameter | Classical Computing | Quantum Computing |
| :--- | :--- | :--- |
| **Basic Unit** | Bit (0 or 1) | Qubit (0, 1, or both) |
| **Pillar** | Boolean Logic | Superposition & Entanglement |
| **Use Cases** | Databases, Browsing, Math | Cryptography, Simulation, Optimization |`,

  scifi: `The rain in Neo-Tokyo did not just fall; it calculated.

> "Every droplet is a node, every gutter is a bus, and the streets are a living, fluid memory engine."
> — *Dr. Akira Vance, Cybernetics Specialist*

The city was built on **Neural Mesh Intelligence**, an aqueous chemical AI weave that responded to the steps of citizens in real-time. It glowed in soft indigo patterns, self-cleaned environmental toxins, and whispered network answers directly to augmented neural Links.

#### Chronology of Fluid AI
1. **2041**: Creation of *Hydro-Synthetics* for cooling heavy quantum nodes.
2. **2049**: Accidental neural routing within the coolant loops, sparking the first fluid intelligence spark.
3. **2055**: Complete integration of edge liquid cores across Neo-Tokyo.

Kenji watched the glowing water stream down the glass pane of his interface. It began to draw code blocks in glowing neon:
\`\`\`javascript
const city = new LiquidGrid({
  nodes: 8400000,
  fluidity: 0.98,
  glow: "cyan-indigo"
});

city.on("pulse", (wave) => {
  optimizeTraffic(wave);
});
\`\`\`
He looked up into the neon-lit horizon, ready to make his next edit.`,

  analyze: `### Comparative Database Analysis for High-Frequency Systems

Evaluating decentralized databases versus standard single-master replication models for low-latency multiplayer syncing:

* **Decentralized Multi-Master (e.g. Cassandra, DynamoDB edge)**:
  * **Pros**:
    * Zero single point of fail-stop boundaries.
    * Writes execute at the nearest regional edge replicas.
  * **Cons**:
    * Eventual consistency latency (nodes require consensus sync intervals).
    * Write conflicts require complex vector-clock reconciliations.
* **Single-Master with Global Edge Reads (e.g. Postgres Replicas)**:
  * **Pros**:
    * Strict consistency for critical operations (like payments or auth).
  * **Cons**:
    * Writes require traveling back to the master region, introducing latency.

---

### Sync Performance Summary
| Metric | Decentralized Engine | Single-Master Engine |
| :--- | :--- | :--- |
| **Write Latency** | **Low (edge-level)** | High (centralized master) |
| **Data Consistency** | Eventual | **Strict / Atomic** |
| **Setup Complexity** | High | Medium |`
};

export function streamAssistantResponse(
  prompt: string,
  history: Message[],
  options: StreamOptions
): StreamController {
  const model = options.model || "intelligence";
  const lowerPrompt = prompt.toLowerCase();
  
  // 1. Choose Response template
  let responseText = MOCK_RESPONSES.default;
  if (lowerPrompt.includes("build") || lowerPrompt.includes("react") || lowerPrompt.includes("code") || lowerPrompt.includes("api")) {
    responseText = MOCK_RESPONSES.code;
  } else if (lowerPrompt.includes("quantum")) {
    responseText = MOCK_RESPONSES.quantum;
  } else if (lowerPrompt.includes("story") || lowerPrompt.includes("sci-fi") || lowerPrompt.includes("liquid")) {
    responseText = MOCK_RESPONSES.scifi;
  } else if (lowerPrompt.includes("analyze") || lowerPrompt.includes("database") || lowerPrompt.includes("pros")) {
    responseText = MOCK_RESPONSES.analyze;
  }

  // 2. Adjust streaming parameters based on model
  let speed = 25; // ms per chunk
  let chunkCharCount = 6; // characters per chunk
  let thinkingTime = 1200; // time in ms before streaming starts

  if (model === "fast") {
    speed = 10;
    chunkCharCount = 12;
    thinkingTime = 400;
  } else if (model === "reason") {
    speed = 35;
    chunkCharCount = 4;
    thinkingTime = 2500;
    // Prefix reasoning thoughts
    responseText = `<thinking>
- Analyzing query parameters: "${prompt.substring(0, 40)}..."
- Correlating concepts against local training models.
- Synthesizing structural markdown syntax layout.
- Finalizing code blocks and technical terminology.
</thinking>

` + responseText;
  }

  let index = 0;
  let intervalId: NodeJS.Timeout | null = null;

  // Simulate thinking phase
  const startTimeout = setTimeout(() => {
    intervalId = setInterval(() => {
      index += chunkCharCount;
      const chunk = responseText.substring(0, index);
      options.onChunk(chunk);

      if (index >= responseText.length) {
        if (intervalId) clearInterval(intervalId);
        options.onComplete(responseText);
      }
    }, speed);
  }, thinkingTime);

  // Return controller with stop method
  return {
    stop: () => {
      clearTimeout(startTimeout);
      if (intervalId) {
        clearInterval(intervalId);
      }
      const partialText = responseText.substring(0, index);
      options.onComplete(partialText || "Generation stopped.");
    },
  };
}
