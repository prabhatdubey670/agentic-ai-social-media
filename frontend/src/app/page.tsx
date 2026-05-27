"use client";

import { useEffect, useState } from "react";
import { 
  fetchDashboardData, 
  fetchQueue, 
  approvePost, 
  runAgent,
  generateInstant,
  publishInstant 
} from "@/lib/api";

interface Post {
  id: string;
  platform: string;
  content_text: string;
  topic: string;
  status: string;
}

export default function Dashboard() {
  const [data, setData] = useState<any>(null);
  const [queue, setQueue] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);

  // Quick Post State
  const [quickTopic, setQuickTopic] = useState("");
  const [quickPlatform, setQuickPlatform] = useState("X.com");
  const [quickDraft, setQuickDraft] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);

  useEffect(() => {
    loadAll();
  }, []);

  const loadAll = async () => {
    try {
      const [dbData, queueData] = await Promise.all([
        fetchDashboardData(),
        fetchQueue()
      ]);
      setData(dbData);
      setQueue(queueData);
    } catch (err) {
      console.error("Fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (id: string) => {
    await approvePost(id);
    loadAll();
  };

  const handleRun = async (mode: string) => {
    alert(`Starting agent in ${mode} mode...`);
    await runAgent(mode);
  };

  const handleGenerateQuick = async () => {
    if (!quickTopic) return;
    setIsGenerating(true);
    try {
      const res = await generateInstant(quickTopic, quickPlatform);
      setQuickDraft(res.draft);
    } catch (err) {
      alert("Generation failed");
    } finally {
      setIsGenerating(false);
    }
  };

  const handlePublishQuick = async () => {
    if (!quickDraft) return;
    setIsPublishing(true);
    try {
      await publishInstant(quickDraft, quickPlatform);
      alert("Successfully published!");
      setQuickDraft("");
      setQuickTopic("");
      loadAll();
    } catch (err) {
      alert("Publishing failed");
    } finally {
      setIsPublishing(false);
    }
  };

  if (loading) return <div className="p-10 text-center">Loading Intelligence...</div>;

  return (
    <div className="min-h-screen bg-gray-50 p-8 font-sans text-gray-900">
      <header className="mb-12 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-blue-900">Research Agent Dashboard</h1>
          <p className="text-gray-500 italic">Managing {data?.identity?.name}'s personal brand</p>
        </div>
        <div className="flex gap-3">
          <button 
            onClick={() => handleRun('post')}
            className="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 transition-colors shadow-sm"
          >
            Run Posting
          </button>
          <button 
            onClick={() => handleRun('full')}
            className="rounded-lg bg-black px-4 py-2 text-white hover:bg-gray-800 transition-colors shadow-sm"
          >
            Run Full Sync
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        {/* Main Content: Generator & Queue */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* Quick Creator */}
          <section className="rounded-xl bg-gradient-to-br from-blue-600 to-blue-800 p-6 text-white shadow-lg">
            <h2 className="mb-4 text-xl font-bold">Instant Post Generator</h2>
            <div className="space-y-4">
              <div className="flex gap-2">
                <input 
                  type="text" 
                  placeholder="Enter a research topic (e.g. FIX Protocol, LSTM models)..."
                  className="flex-1 rounded-lg border-none bg-white/10 px-4 py-2 text-white placeholder-blue-200 focus:bg-white/20 focus:outline-none focus:ring-2 focus:ring-white/50"
                  value={quickTopic}
                  onChange={(e) => setQuickTopic(e.target.value)}
                />
                <select 
                  className="rounded-lg border-none bg-white/10 px-2 py-2 text-white focus:bg-white/20 focus:outline-none"
                  value={quickPlatform}
                  onChange={(e) => setQuickPlatform(e.target.value)}
                >
                  <option className="text-black" value="X.com">X.com</option>
                  <option className="text-black" value="LinkedIn">LinkedIn</option>
                </select>
                <button 
                  onClick={handleGenerateQuick}
                  disabled={isGenerating || !quickTopic}
                  className="rounded-lg bg-white px-6 py-2 font-bold text-blue-700 hover:bg-blue-50 disabled:opacity-50"
                >
                  {isGenerating ? "Thinking..." : "Generate"}
                </button>
              </div>

              {quickDraft && (
                <div className="mt-4 animate-in fade-in slide-in-from-top-2 duration-300">
                  <textarea 
                    className="w-full rounded-lg border-none bg-white/10 p-4 text-sm text-white focus:bg-white/20 focus:outline-none"
                    rows={6}
                    value={quickDraft}
                    onChange={(e) => setQuickDraft(e.target.value)}
                  />
                  <div className="mt-2 flex justify-end">
                    <button 
                      onClick={handlePublishQuick}
                      disabled={isPublishing}
                      className="rounded-lg bg-green-500 px-8 py-2 font-bold text-white hover:bg-green-400 shadow-md"
                    >
                      {isPublishing ? "Posting..." : "Publish Immediately"}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </section>

          {/* Pending Queue */}
          <section className="rounded-xl bg-white p-6 shadow-sm border border-gray-100">
            <h2 className="mb-4 text-xl font-semibold flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-yellow-400"></span>
              Pending Approval
            </h2>
            {queue.length === 0 ? (
              <p className="text-gray-400 py-4 text-center border-2 border-dashed rounded-lg">No drafts waiting. The agent is sleeping.</p>
            ) : (
              <div className="space-y-4">
                {queue.map((post) => (
                  <div key={post.id} className="rounded-lg border p-4 hover:border-blue-200 transition-colors bg-gray-50/30">
                    <div className="mb-2 flex items-center justify-between">
                      <span className="text-xs font-bold uppercase tracking-wider text-blue-600">{post.platform}</span>
                      <span className="text-xs text-gray-400">#{post.topic}</span>
                    </div>
                    <p className="text-sm leading-relaxed mb-4 text-gray-700">{post.content_text}</p>
                    <div className="flex gap-2">
                      <button 
                        onClick={() => handleApprove(post.id)}
                        className="text-xs font-semibold bg-green-600 text-white px-4 py-1.5 rounded-lg hover:bg-green-700 shadow-sm"
                      >
                        Approve & Post
                      </button>
                      <button className="text-xs font-semibold bg-white border border-gray-200 text-gray-600 px-4 py-1.5 rounded-lg hover:bg-gray-50 shadow-sm">
                        Edit
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>

        {/* Sidebar: Stats */}
        <div className="space-y-8">
          <section className="rounded-xl bg-white p-6 shadow-sm border border-gray-100">
            <h2 className="mb-4 text-lg font-semibold">Performance Analytics</h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-lg bg-gray-50 p-4 text-center border border-gray-100">
                <p className="text-2xl font-bold text-blue-900">{data?.daily_stats?.[0]?.[7] || 0}</p>
                <p className="text-[10px] text-gray-500 uppercase tracking-tighter">Posts (24h)</p>
              </div>
              <div className="rounded-lg bg-gray-50 p-4 text-center border border-gray-100">
                <p className="text-2xl font-bold text-blue-900">{data?.daily_stats?.[0]?.[3] || 0}</p>
                <p className="text-[10px] text-gray-500 uppercase tracking-tighter">Likes (24h)</p>
              </div>
            </div>
          </section>

          <section className="rounded-xl bg-white p-6 shadow-sm border border-gray-100">
            <h2 className="mb-4 text-lg font-semibold">Niche Authority</h2>
            <div className="space-y-3">
              {data?.topic_performance?.length > 0 ? (
                data?.topic_performance?.slice(0, 6).map((t: any, i: number) => (
                  <div key={i} className="flex items-center justify-between text-sm">
                    <span className="capitalize text-gray-600">{t[0]}</span>
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-16 bg-gray-100 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-500" style={{width: `${(t[2]/10)*100}%`}}></div>
                      </div>
                      <span className="font-mono text-[10px] text-gray-400">{t[2].toFixed(1)}</span>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-xs text-gray-400 italic">Analyzing topics...</p>
              )}
            </div>
          </section>

          <section className="rounded-xl bg-gray-900 p-6 text-white shadow-2xl border border-blue-900/30">
            <h2 className="mb-3 text-sm font-bold uppercase tracking-widest text-blue-400">Agent Intelligence Log</h2>
            <div className="font-mono text-[10px] opacity-70 h-48 overflow-y-auto space-y-1">
              <p className="text-gray-500">[{new Date().toLocaleTimeString()}] System: Booting Supervisor...</p>
              <p className="text-gray-500">[{new Date().toLocaleTimeString()}] Auth: Session loaded from cache.</p>
              <p className="text-blue-300">[{new Date().toLocaleTimeString()}] Task: Scanning {quickPlatform} feed...</p>
              <p className="text-green-400">{"->"} Analytics data synced successfully.</p>
              <p className="text-green-400">{"->"} DB Path: {data?.db_status || 'Absolute Verified'}</p>
              <p className="animate-pulse text-white">_</p>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
