"use client";

import { useState } from "react";

type Summary = {
  Patient_Name?: string;
  Symptoms?: string[];
  Diagnosis?: string;
  Treatment?: string[];
  Current_Status?: string;
  Prognosis?: string;
  [key: string]: unknown;
};

type SoapNote = {
  Subjective?: Record<string, unknown>;
  Objective?: Record<string, unknown>;
  Assessment?: Record<string, unknown>;
  Plan?: Record<string, unknown>;
  [key: string]: unknown;
};

type ApiResult = {
  patient_name?: string;
  summary?: Summary;
  keywords?: string[];
  sentiment?: { Sentiment: string; Confidence: number };
  intent?: { Intent: string; Confidence: number };
  soap_note?: SoapNote;
  error?: string;
};

const SAMPLE_TRANSCRIPT = `Physician: Good morning, Ms. Jones. How are you feeling today?
Patient: I'm doing better, but I still have some discomfort now and then.
Physician: I understand you were in a car accident last September. Can you walk me through what happened?
Patient: Yes, it was on September 1st, around 12:30 in the afternoon. I was driving from Cheadle Hulme to Manchester when I had to stop in traffic. Out of nowhere, another car hit me from behind, which pushed my car into the one in front.
Physician: That sounds like a strong impact. Were you wearing your seatbelt?
Patient: Yes, I always do.
Physician: What did you feel immediately after the accident?
Patient: At first, I was just shocked. But then I realized I had hit my head on the steering wheel, and I could feel pain in my neck and back almost right away.
Physician: Did you seek medical attention at that time?
Patient: Yes, I went to Moss Bank Accident and Emergency. They checked me over and said it was a whiplash injury, but they didn't do any X-rays. They just gave me some advice and sent me home.
Physician: How did things progress after that?
Patient: The first four weeks were rough. My neck and back pain were really bad—I had trouble sleeping and had to take painkillers regularly. It started improving after that, but I had to go through ten sessions of physiotherapy to help with the stiffness and discomfort.
Physician: That makes sense. Are you still experiencing pain now?
Patient: It's not constant, but I do get occasional backaches. It's nothing like before, though.
Physician: That's good to hear. Have you noticed any other effects, like anxiety while driving or difficulty concentrating?
Patient: No, nothing like that. I don't feel nervous driving, and I haven't had any emotional issues from the accident.
Physician: And how has this impacted your daily life? Work, hobbies, anything like that?
Patient: I had to take a week off work, but after that, I was back to my usual routine. It hasn't really stopped me from doing anything.
Physician: Everything looks good. Your neck and back have a full range of movement, and there's no tenderness or signs of lasting damage. Your muscles and spine seem to be in good condition.
Physician: Given your progress, I'd expect you to make a full recovery within six months of the accident.`;

export default function Page() {
  const [transcript, setTranscript] = useState(SAMPLE_TRANSCRIPT);
  const [patientName, setPatientName] = useState("Janet Jones");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ApiResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    let timeoutId: NodeJS.Timeout | undefined;
    try {
      const controller = new AbortController();
      timeoutId = setTimeout(() => controller.abort(), 180000); // 3 minutes timeout
      
      const res = await fetch(`${backendUrl}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transcript, patient_name: patientName || undefined }),
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (!res.ok) {
        const errorText = await res.text();
        let errorMsg = `HTTP ${res.status}: ${res.statusText}`;
        try {
          const errorJson = JSON.parse(errorText);
          errorMsg = errorJson.error || errorJson.detail || errorMsg;
        } catch {
          errorMsg = errorText || errorMsg;
        }
        throw new Error(errorMsg);
      }
      
      const data: ApiResult = await res.json();
      if (data.error) {
        throw new Error(data.error);
      }
      setResult(data);
    } catch (err) {
      if ((err as Error).name === 'AbortError') {
        setError("Request timed out (3 minutes). Backend may be slow. Try a smaller model or Groq API.");
      } else if (err instanceof TypeError && err.message.includes("fetch")) {
        setError(`Cannot connect to backend at ${backendUrl}. Make sure the backend is running and accessible.`);
      } else {
        setError((err as Error).message);
      }
      setResult(null);
    } finally {
      setLoading(false);
      if (timeoutId) clearTimeout(timeoutId);
    }
  };

  return (
    <main className="grid gap-8" style={{ position: "relative", zIndex: 1 }}>
      <header className="grid gap-4 text-center">
        <div>
          <p className="text-sm uppercase tracking-[0.35em] mb-2" style={{ color: "rgba(100, 116, 139, 0.8)" }}>Physician Notetaker</p>
          <h1 className="text-4xl md:text-5xl font-bold mb-3" style={{
            background: "linear-gradient(135deg, #2563eb, #7c3aed, #2563eb)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text"
          }}>
            Medical NLP Summarizer
          </h1>
          <h2 className="text-xl font-medium" style={{ color: "#475569" }}>SOAP Note Generator</h2>
        </div>
        <p className="max-w-2xl mx-auto" style={{ color: "#64748b" }}>
          Extract key medical details, analyze patient sentiment and intent, and generate structured SOAP notes from physician-patient conversations.
        </p>
        {/* <div className="text-xs mt-2" style={{ color: "rgba(100, 116, 139, 0.7)" }}>
          Backend: <code style={{ color: "#475569" }}>{backendUrl}</code>
        </div> */}
      </header>

      <section className="card grid gap-6">
        <div className="grid two-col gap-6">
          <div className="grid gap-3">
            <label className="text-sm font-medium flex items-center gap-2" style={{ color: "#475569" }}>
              <span className="w-2 h-2 rounded-full" style={{ background: "#3b82f6" }}></span>
              Patient Name <span className="font-normal" style={{ color: "rgba(100, 116, 139, 0.7)" }}>(optional)</span>
            </label>
            <input
              className="input"
              value={patientName}
              onChange={(e) => setPatientName(e.target.value)}
              placeholder="e.g., Janet Jones"
            />
          </div>
          <div className="grid gap-3">
            <label className="text-sm font-medium flex items-center gap-2" style={{ color: "#475569" }}>
              <span className="w-2 h-2 rounded-full" style={{ background: "#8b5cf6" }}></span>
              Conversation Transcript
            </label>
            <textarea
              className="input"
              rows={14}
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
              placeholder="Paste physician-patient conversation transcript here..."
            />
          </div>
        </div>
        <div className="flex gap-4 items-center pt-2">
          <button className="btn" onClick={handleSubmit} disabled={loading}>
            {loading ? (
              <>
                <span className="spinner"></span>
                Processing...
              </>
            ) : (
              "Analyze Transcript"
            )}
          </button>
          {error && (
            <div className="error-message flex-1">
              <span>⚠️</span>
              <span>{error}</span>
            </div>
          )}
        </div>
      </section>

      {result && (
        <section className="grid gap-6">
          {/* Stats Overview */}
          <div className="card">
            <div className="stats-grid">
              <div className="stat-item">
                <div className="stat-label">Patient</div>
                <div className="stat-value">{result.patient_name || "Unknown"}</div>
              </div>
              <div className="stat-item">
                <div className="stat-label">Sentiment</div>
                <div className="stat-value">
                  <span className={`badge ${result.sentiment?.Sentiment === "Reassured" ? "badge-success" : result.sentiment?.Sentiment === "Anxious" ? "badge-warning" : ""}`}>
                    {result.sentiment?.Sentiment || "Neutral"}
                  </span>
                  <span style={{ fontSize: "12px", color: "rgba(148, 163, 184, 0.6)", marginLeft: "8px" }}>
                    ({(result.sentiment?.Confidence || 0).toFixed(2)})
                  </span>
                </div>
              </div>
              <div className="stat-item">
                <div className="stat-label">Intent</div>
                <div className="stat-value">
                  {result.intent?.Intent || "Unknown"}
                  <span style={{ fontSize: "12px", color: "rgba(148, 163, 184, 0.6)", marginLeft: "8px" }}>
                    ({(result.intent?.Confidence || 0).toFixed(2)})
                  </span>
                </div>
              </div>
              <div className="stat-item">
                <div className="stat-label">Keywords</div>
                <div className="stat-value">{result.keywords?.length || 0} extracted</div>
              </div>
            </div>
          </div>

          {/* Main Results Grid */}
          <div className="grid two-col gap-6">
            {/* Summary Card */}
            <div className="card">
              <div className="section-header">
                <h3>Medical Summary</h3>
              </div>
              <div className="json-display">
                <pre style={{ margin: 0, whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
                  {JSON.stringify(result.summary, null, 2)}
                </pre>
              </div>
              {result.keywords && result.keywords.length > 0 && (
                <div style={{ marginTop: "16px", paddingTop: "16px", borderTop: "1px solid rgba(148, 163, 184, 0.2)" }}>
                  <div className="text-sm font-medium" style={{ marginBottom: "12px", color: "#475569" }}>Key Medical Terms</div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                    {result.keywords.map((kw, idx) => (
                      <span key={idx} className="keyword-tag">{kw}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* SOAP Note Card */}
            <div className="card">
              <div className="section-header">
                <h3>SOAP Note</h3>
              </div>
              <div className="json-display">
                <pre style={{ margin: 0, whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
                  {JSON.stringify(result.soap_note, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        </section>
      )}
    </main>
  );
}

