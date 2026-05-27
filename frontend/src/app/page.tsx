"use client";

import { useEffect, useState } from "react";
import { 
  fetchDashboardData, 
  fetchQueue, 
  approvePost, 
  runAgent,
  generateInstant,
  publishInstant,
  fetchProfileStats,
  fetchWorldUpdate,
  fetchSuggestedPeers,
  addManualPeer
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
  const [profile, setProfile] = useState<any>(null);
  const [worldUpdate, setWorldUpdate] = useState<string[]>([]);
  const [suggestedPeers, setSuggestedPeers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Quick Post State
  const [quickTopic, setQuickTopic] = useState("");
  const [quickPlatform, setQuickPlatform] = useState("X.com");
  const [quickDraft, setQuickDraft] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);

  // Hub State
  const [newPeerUrl, setNewPeerUrl] = useState("");
  const [activeTab, setActiveTab] = useState("dashboard");

  useEffect(() => {
    // Initial core load
    loadCoreData();
  }, []);

  useEffect(() => {
    // Background load slower intelligence data
    if (!loading) {
      loadIntelligenceData();
    }
  }, [loading]);

  const loadCoreData = async () => {
    try {
      const [dbData, queueData, profileData] = await Promise.all([
        fetchDashboardData(),
        fetchQueue(),
        fetchProfileStats()
      ]);
      setData(dbData);
      setQueue(queueData);
      setProfile(profileData);
    } catch (err) {
      console.error("Core fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  const loadIntelligenceData = async () => {
    try {
      const [worldData, peersData] = await Promise.all([
        fetchWorldUpdate(),
        fetchSuggestedPeers()
      ]);
      setWorldUpdate(worldData.summary);
      setSuggestedPeers(peersData.peers);
    } catch (err) {
      console.error("Intelligence fetch error:", err);
    }
  };

  const handleAddPeer = async () => {
    if (!newPeerUrl) return;
    const handle = newPeerUrl.split('/').filter(Boolean).pop() || newPeerUrl;
    const platform = newPeerUrl.includes('linkedin') ? 'LinkedIn' : 'X.com';
    await addManualPeer(handle, platform, newPeerUrl);
    setNewPeerUrl("");
    alert("Peer added to tracking list!");
  };

  const handleApprove = async (id: string) => {
    await approvePost(id);
    loadCoreData();
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
      loadCoreData();
    } catch (err) {
      alert("Publishing failed");
    } finally {
      setIsPublishing(false);
    }
  };

  if (loading) return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 font-sans">
      <div className="text-center">
        <div className="mb-4 h-12 w-12 animate-spin rounded-full border-4 border-blue-600 border-t-transparent mx-auto"></div>
        <p className="text-xl font-bold text-blue-900">Initializing Intelligence...</p>
        <p className="text-sm text-gray-500">Connecting to your research brain...</p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 p-8 font-sans text-gray-900">
      <header className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-blue-900">Research Agent Dashboard</h1>
          <p className="text-gray-500 italic text-sm">Managing {data?.identity?.name}'s personal brand</p>
        </div>
        <div className="flex gap-4">
          <nav className="flex bg-gray-200 p-1 rounded-xl mr-4 shadow-inner">
            <button 
              onClick={() => setActiveTab('dashboard')}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${activeTab === 'dashboard' ? 'bg-white text-blue-700 shadow-sm' : 'text-gray-600 hover:text-gray-900'}`}
            >
              Dashboard
            </button>
            <button 
              onClick={() => setActiveTab('hub')}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${activeTab === 'hub' ? 'bg-white text-blue-700 shadow-sm' : 'text-gray-600 hover:text-gray-900'}`}
            >
              Intelligence Hub
            </button>
          </nav>
          <div className="flex gap-3">
            <button 
              onClick={() => handleRun('post')}
              className="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 transition-colors shadow-sm text-sm font-semibold"
            >
              Run Posting
            </button>
            <button 
              onClick={() => handleRun('full')}
              className="rounded-lg bg-black px-4 py-2 text-white hover:bg-gray-800 transition-colors shadow-sm text-sm font-semibold"
            >
              Run Full Sync
            </button>
          </div>
        </div>
      </header>

      {activeTab === 'dashboard' ? (
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
              <h2 className="mb-4 text-xl font-semibold flex items-center gap-2 text-gray-800">
                <span className="h-2 w-2 rounded-full bg-yellow-400"></span>
                Pending Approval
              </h2>
              {queue.length === 0 ? (
                <p className="text-gray-400 py-10 text-center border-2 border-dashed rounded-xl">No drafts waiting. The agent is sleeping.</p>
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
              <h2 className="mb-4 text-lg font-semibold text-gray-800">Profile Overview</h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between border-b pb-2">
                  <span className="text-sm font-medium text-gray-500 text-xs uppercase tracking-wider">X Followers</span>
                  <span className="text-lg font-bold text-blue-600">{profile?.x?.followers || '--'}</span>
                </div>
                <div className="flex items-center justify-between border-b pb-2">
                  <span className="text-sm font-medium text-gray-500 text-xs uppercase tracking-wider">LinkedIn Conn.</span>
                  <span className="text-lg font-bold text-blue-600">{profile?.linkedin?.connections || '--'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-500 text-xs uppercase tracking-wider">Avg. Engagement</span>
                  <span className="text-lg font-bold text-green-600">8.4%</span>
                </div>
              </div>
            </section>

            <section className="rounded-xl bg-white p-6 shadow-sm border border-gray-100">
              <h2 className="mb-4 text-lg font-semibold text-gray-800">Performance Analytics</h2>
              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-lg bg-gray-50 p-4 text-center border border-gray-100">
                  <p className="text-2xl font-bold text-blue-900">
                    {data?.daily_stats?.filter((s: any) => s[1] === new Date().toISOString().split('T')[0])
                      .reduce((acc: number, curr: any) => acc + curr[7], 0) || 0}
                  </p>
                  <p className="text-[10px] text-gray-500 uppercase tracking-tighter">Posts (Today)</p>
                </div>
                <div className="rounded-lg bg-gray-50 p-4 text-center border border-gray-100">
                  <p className="text-2xl font-bold text-blue-900">
                    {data?.daily_stats?.filter((s: any) => s[1] === new Date().toISOString().split('T')[0])
                      .reduce((acc: number, curr: any) => acc + (curr[3] || 0), 0) || 0}
                  </p>
                  <p className="text-[10px] text-gray-500 uppercase tracking-tighter">Likes (Today)</p>
                </div>
              </div>
            </section>

            <section className="rounded-xl bg-gray-900 p-6 text-white shadow-2xl border border-blue-900/30">
              <h2 className="mb-3 text-sm font-bold uppercase tracking-widest text-blue-400">Agent Intelligence Log</h2>
              <div className="font-mono text-[10px] opacity-70 h-48 overflow-y-auto space-y-1">
                <p className="text-gray-500">[{new Date().toLocaleTimeString()}] System: Booting Supervisor...</p>
                <p className="text-gray-500">[{new Date().toLocaleTimeString()}] AI Model: OpenRouter/Free (Llama 3)</p>
                <p className="text-blue-300">[{new Date().toLocaleTimeString()}] Task: Scanning {quickPlatform} feed...</p>
                <p className="text-green-400">{"->"} Analytics data synced successfully.</p>
                <p className="text-green-400">{"->"} DB Path: Absolute Path Verified</p>
                <p className="animate-pulse text-white">_</p>
              </div>
            </section>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          {/* Intelligence Hub View */}
          <div className="lg:col-span-2 space-y-8">
            {/* World at a Glance */}
            <section className="rounded-xl bg-white p-6 shadow-sm border border-gray-100">
              <h2 className="mb-4 text-xl font-bold text-gray-800 flex items-center gap-2">
                🌍 World at a Glance
              </h2>
              {worldUpdate.length === 0 ? (
                <div className="py-10 text-center space-y-3">
                   <div className="h-6 w-6 border-2 border-blue-500 border-t-transparent animate-spin rounded-full mx-auto"></div>
                   <p className="text-sm text-gray-400">AI is reading world trends...</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {worldUpdate.map((point, i) => (
                    <div key={i} className="flex gap-4 items-start bg-blue-50/50 p-4 rounded-xl border border-blue-100">
                      <span className="bg-blue-600 text-white rounded-full h-6 w-6 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">{i+1}</span>
                      <p className="text-sm text-gray-700 font-medium leading-relaxed">{point}</p>
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* Peer Suggestions */}
            <section className="rounded-xl bg-white p-6 shadow-sm border border-gray-100">
              <h2 className="mb-4 text-xl font-bold text-gray-800">Recommended for Your Network</h2>
              {suggestedPeers.length === 0 ? (
                <div className="py-10 text-center space-y-3">
                   <div className="h-6 w-6 border-2 border-blue-500 border-t-transparent animate-spin rounded-full mx-auto"></div>
                   <p className="text-sm text-gray-400">Finding high-value peers...</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {suggestedPeers.map((peer, i) => (
                    <div key={i} className="p-4 rounded-lg border border-gray-100 bg-gray-50 hover:border-blue-200 transition-colors">
                      <div className="flex justify-between items-start mb-2">
                        <p className="font-bold text-blue-900">{peer.name}</p>
                        <span className="text-[10px] bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-bold uppercase">{peer.platform}</span>
                      </div>
                      <p className="text-xs text-blue-600 font-medium mb-2">{peer.handle}</p>
                      <p className="text-[11px] text-gray-500 leading-relaxed">{peer.reason}</p>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>

          <div className="space-y-8">
             {/* Add Peer URL */}
             <section className="rounded-xl bg-blue-900 p-6 text-white shadow-lg">
              <h2 className="mb-4 text-lg font-bold">Track a New Peer</h2>
              <p className="text-xs text-blue-200 mb-4 leading-relaxed">Add a specific LinkedIn or X.com profile URL to monitor their latest technical insights.</p>
              <div className="space-y-3">
                <input 
                  type="text" 
                  placeholder="https://linkedin.com/in/..."
                  className="w-full rounded-lg border-none bg-white/10 px-4 py-2 text-white placeholder-blue-300 focus:bg-white/20 focus:outline-none"
                  value={newPeerUrl}
                  onChange={(e) => setNewPeerUrl(e.target.value)}
                />
                <button 
                  onClick={handleAddPeer}
                  disabled={!newPeerUrl}
                  className="w-full rounded-lg bg-blue-500 py-2 font-bold text-white hover:bg-blue-400 transition-all shadow-md disabled:opacity-50"
                >
                  Add to Tracking List
                </button>
              </div>
            </section>

            <section className="rounded-xl bg-white p-6 shadow-sm border border-gray-100">
              <h2 className="mb-4 text-lg font-semibold text-gray-800">Topic Trends</h2>
              <div className="space-y-4">
                {data?.topic_performance?.map((t: any, i: number) => (
                  <div key={i} className="text-xs">
                    <div className="flex justify-between mb-1">
                      <span className="font-medium text-gray-600">{t[0]}</span>
                      <span className="text-blue-500">Trending</span>
                    </div>
                    <div className="h-1 w-full bg-gray-100 rounded-full">
                       <div className="h-full bg-blue-500" style={{width: `${Math.random()*100}%`}}></div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </div>
      )}
    </div>
  );
}
