"use client";

import { useEffect, useState } from "react";
import { fetchDashboardData, fetchQueue, approvePost, runAgent } from "@/lib/api";

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
      console.error(err);
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

  if (loading) return <div className="p-10 text-center">Loading Intelligence...</div>;

  return (
    <div className="min-h-screen bg-gray-50 p-8 font-sans text-gray-900">
      <header className="mb-12 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AI Social Manager</h1>
          <p className="text-gray-500 italic">Managing {data?.identity?.name}'s personal brand</p>
        </div>
        <div className="flex gap-3">
          <button 
            onClick={() => handleRun('post')}
            className="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 transition-colors"
          >
            Run Posting
          </button>
          <button 
            onClick={() => handleRun('full')}
            className="rounded-lg bg-black px-4 py-2 text-white hover:bg-gray-800 transition-colors"
          >
            Run Full Sync
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        {/* Main Content: Queue */}
        <div className="lg:col-span-2 space-y-8">
          <section className="rounded-xl bg-white p-6 shadow-sm border border-gray-100">
            <h2 className="mb-4 text-xl font-semibold">Pending Approval</h2>
            {queue.length === 0 ? (
              <p className="text-gray-400 py-4">No drafts waiting. The agent is sleeping.</p>
            ) : (
              <div className="space-y-4">
                {queue.map((post) => (
                  <div key={post.id} className="rounded-lg border p-4 hover:border-blue-200 transition-colors">
                    <div className="mb-2 flex items-center justify-between">
                      <span className="text-xs font-bold uppercase tracking-wider text-blue-600">{post.platform}</span>
                      <span className="text-xs text-gray-400">#{post.topic}</span>
                    </div>
                    <p className="text-sm leading-relaxed mb-4">{post.content_text}</p>
                    <div className="flex gap-2">
                      <button 
                        onClick={() => handleApprove(post.id)}
                        className="text-xs font-semibold bg-green-50 text-green-700 px-3 py-1 rounded-full hover:bg-green-100"
                      >
                        Approve & Post
                      </button>
                      <button className="text-xs font-semibold bg-gray-50 text-gray-600 px-3 py-1 rounded-full hover:bg-gray-100">
                        Edit
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          <section className="rounded-xl bg-white p-6 shadow-sm border border-gray-100">
            <h2 className="mb-4 text-xl font-semibold">Recent Insights</h2>
            <div className="space-y-4">
              {data?.recent_strategies?.map((s: any, i: number) => (
                <div key={i} className="text-sm border-l-4 border-blue-500 pl-4 py-1">
                  <p className="font-medium">{s[0]}</p>
                  <p className="text-gray-500 line-clamp-1 italic">{s[1]}</p>
                </div>
              ))}
            </div>
          </section>
        </div>

        {/* Sidebar: Stats */}
        <div className="space-y-8">
          <section className="rounded-xl bg-white p-6 shadow-sm border border-gray-100">
            <h2 className="mb-4 text-lg font-semibold">Growth Metrics</h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-lg bg-gray-50 p-4 text-center">
                <p className="text-2xl font-bold">--</p>
                <p className="text-xs text-gray-500 uppercase">Followers</p>
              </div>
              <div className="rounded-lg bg-gray-50 p-4 text-center">
                <p className="text-2xl font-bold">{data?.daily_stats?.[0]?.[3] || 0}</p>
                <p className="text-xs text-gray-500 uppercase">Likes (24h)</p>
              </div>
            </div>
          </section>

          <section className="rounded-xl bg-white p-6 shadow-sm border border-gray-100">
            <h2 className="mb-4 text-lg font-semibold">Top Topics</h2>
            <div className="space-y-3">
              {data?.topic_performance?.slice(0, 5).map((t: any, i: number) => (
                <div key={i} className="flex items-center justify-between text-sm">
                  <span className="capitalize text-gray-700">{t[0]}</span>
                  <span className="font-mono text-gray-400">{t[2].toFixed(1)}</span>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-xl bg-black p-6 text-white shadow-lg">
            <h2 className="mb-2 text-lg font-semibold underline decoration-blue-500">Live Agent Logs</h2>
            <div className="font-mono text-[10px] opacity-70 h-32 overflow-y-auto">
              <p>[INFO] Supervisor initialized...</p>
              <p>[INFO] X.com API connected.</p>
              <p>[INFO] Searching for topics: ML, HFT...</p>
              <p className="text-blue-400">{"->"} Found post by @quant_guru</p>
              <p className="text-green-400">{"->"} AI analysis: High value (Score: 8)</p>
              <p>...</p>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
