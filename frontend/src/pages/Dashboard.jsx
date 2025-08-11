import React, { useState, useEffect } from "react";
import StatCard from "../components/StatCard";
import {
    LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import {
    getSummary,
    getActivity,
    getContent,
    getTimeline,
    getVisualizations
} from "../api/whatsapp";

function Dashboard({ sessionId, sessionFilename }) {
    const [tab, setTab] = useState("summary");

    const [summary, setSummary] = useState(null);
    const [activity, setActivity] = useState(null);
    const [content, setContent] = useState(null);
    const [timeline, setTimeline] = useState(null);
    const [visualizations, setVisualizations] = useState(null);

    const [loading, setLoading] = useState(false);
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 1;

    const visualizationItems = [
        { key: "weekday_chart", label: "Weekday Chart", data: visualizations?.weekday_chart },
        { key: "month_chart", label: "Month Chart", data: visualizations?.month_chart },
        { key: "timeline_chart", label: "Timeline Chart", data: visualizations?.timeline_chart },
        { key: "pie_chart", label: "Pie Chart", data: visualizations?.pie_chart },
        { key: "wordcloud", label: "Word Cloud", data: visualizations?.wordcloud },
    ].filter(item => item.data);

    const totalPages = Math.ceil(visualizationItems.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const currentItems = visualizationItems.slice(startIndex, startIndex + itemsPerPage);

    // Prepare overall activity data for charts (safe checks)
    const hourlyData = activity?.overall?.hourly_activity
        ? Object.entries(activity.overall.hourly_activity).map(([hour, count]) => ({
            hour: `${hour}:00`,
            count,
        }))
        : [];

    const dailyData = activity?.overall?.daily_activity
        ? Object.entries(activity.overall.daily_activity).map(([day, count]) => ({
            day,
            count,
        }))
        : [];

    const monthlyData = activity?.overall?.monthly_activity
        ? Object.entries(activity.overall.monthly_activity).map(([month, count]) => ({
            month,
            count,
        }))
        : [];

    // Prepare per-person activity data for charts
    const personsActivity = activity?.by_person
        ? Object.entries(activity?.by_person).map(([person, stats]) => ({
            person,
            hourlyData: Object.entries(stats.hourly).map(([hour, count]) => ({
                hour: `${hour}:00`,
                count,
            })),
            dailyData: Object.entries(stats.daily).map(([day, count]) => ({
                day,
                count,
            })),
            monthlyData: Object.entries(stats.monthly).map(([month, count]) => ({
                month,
                count,
            })),
        }))
        : [];

    // Overall timeline data
    const overallTimelineData = timeline?.overall?.map(item => ({
        date: item.date,
        count: item.count
    })) || [];

    // Per-person timeline data
    const personsTimelineData = timeline?.by_person
        ? Object.entries(timeline.by_person).map(([person, arr]) => ({
            person,
            data: arr.map(item => ({
                date: item.date,
                count: item.count
            }))
        }))
        : [];


    // Fetch data based on selected tab
    useEffect(() => {
        if (!sessionId) return;
        setLoading(true);

        let fetchFn;

        switch (tab) {
            case "summary":
                fetchFn = () => getSummary(sessionId).then(setSummary);
                break;
            case "activity":
                fetchFn = () => getActivity(sessionId).then(setActivity);
                break;
            case "content":
                fetchFn = () => getContent(sessionId).then(setContent);
                break;
            case "timeline":
                fetchFn = () => getTimeline(sessionId, "daily").then(setTimeline);
                break;
            case "visualizations":
                fetchFn = () => getVisualizations(sessionId).then(setVisualizations);
                break;
            default:
                fetchFn = null;
        }

        if (fetchFn) {
            fetchFn().finally(() => setLoading(false));
        }
    }, [tab, sessionId]);

    return (
        <div className="container mx-auto py-4">
            <h2 className="text-xl font-bold mb-2">
                Chat Analysis for: {sessionFilename}
            </h2>

            {/* Tabs */}
            <div className="flex space-x-4 mb-4">
                <button
                    onClick={() => setTab("summary")}
                    className={tab === "summary" ? "underline font-bold" : ""}
                >
                    Summary
                </button>
                <button
                    onClick={() => setTab("activity")}
                    className={tab === "activity" ? "underline font-bold" : ""}
                >
                    Activity
                </button>
                <button
                    onClick={() => setTab("timeline")}
                    className={tab === "timeline" ? "underline font-bold" : ""}
                >
                    Timeline
                </button>
                <button
                    onClick={() => setTab("visualizations")}
                    className={tab === "visualizations" ? "underline font-bold" : ""}
                >
                    More Visualizations
                </button>
            </div>

            {/* Loading */}
            {loading && <p className="text-center text-gray-600">Loading...</p>}

            {/* Summary Tab */}
            {tab === "summary" && summary && (
                <div className="space-y-6">
                    {/* Stat Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <StatCard label="Total Messages" value={summary.total_messages} />
                        <StatCard label="Unique Users" value={summary.unique_users} />
                        <StatCard
                            label="Date Range"
                            value={`${new Date(summary.date_range.start).toLocaleDateString()} - ${new Date(summary.date_range.end).toLocaleDateString()}`}
                        />
                        <StatCard label="Avg Message Length" value={`${summary.avg_message_length} chars`} />
                        <StatCard label="Avg Words / Message" value={summary.avg_words_per_message} />
                        <StatCard label="Total URLs Shared" value={summary.total_urls_shared} />
                    </div>

                    {/* Top Senders Table */}
                    <div className="bg-white shadow rounded p-4">
                        <h3 className="text-lg font-bold mb-3">Top Senders</h3>
                        <table className="w-full border-collapse">
                            <thead>
                                <tr className="bg-gray-100">
                                    <th className="p-2 text-left border">Name</th>
                                    <th className="p-2 text-left border">Messages</th>
                                </tr>
                            </thead>
                            <tbody>
                                {Object.entries(summary.top_senders).map(([sender, count]) => (
                                    <tr key={sender}>
                                        <td className="p-2 border">{sender}</td>
                                        <td className="p-2 border">{count}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Activity Tab */}
            {tab === "activity" && activity && (
                <div className="space-y-8">
                    {/* Overall Hourly Chart */}
                    <div className="bg-white rounded shadow p-6">
                        <h3 className="text-xl font-semibold mb-4">Hourly Activity</h3>
                        <ResponsiveContainer width="100%" height={250}>
                            <BarChart data={hourlyData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="hour"
                                    label={{ value: "Hour of the day", position: "insideBottom", offset: 0 }}
                                />
                                <YAxis
                                    label={{ value: "Message Count ", angle: -90, position: "insideLeft", style: { textAnchor: "middle" } }}
                                />
                                <Tooltip />
                                <Bar dataKey="count" fill="#8884d8" />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Overall Daily Chart */}
                    <div className="bg-white rounded shadow p-6">
                        <h3 className="text-xl font-semibold mb-4">Daily Activity</h3>
                        <ResponsiveContainer width="100%" height={250}>
                            <BarChart data={dailyData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="day" />
                                <YAxis
                                    label={{ value: "Message Count ", angle: -90, position: "insideLeft", style: { textAnchor: "middle" }, offset: 10 }}
                                />
                                <Tooltip />
                                <Bar dataKey="count" fill="#82ca9d" />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Overall Monthly Chart */}
                    <div className="bg-white rounded shadow p-6">
                        <h3 className="text-xl font-semibold mb-4">Monthly Activity</h3>
                        <ResponsiveContainer width="100%" height={250}>
                            <BarChart data={monthlyData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="month" />
                                <YAxis
                                    label={{ value: "Message Count ", angle: -90, position: "insideLeft", style: { textAnchor: "middle" }, offset: 10 }} />
                                <Tooltip />
                                <Bar dataKey="count" fill="#ffc658" />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Activity By Person */}
                    {personsActivity.length > 0 && (
                        <>
                            <h3 className="text-2xl font-bold mt-10">Activity by Person</h3>
                            {personsActivity.map(({ person, hourlyData, dailyData, monthlyData }) => (
                                <div key={person} className="mb-8 p-4 border rounded shadow bg-white">
                                    <h4 className="text-lg font-semibold mb-4">{person}</h4>

                                    <div className="mb-6">
                                        <h5>Hourly Activity</h5>
                                        <ResponsiveContainer width="100%" height={200}>
                                            <BarChart data={hourlyData}>
                                                <CartesianGrid strokeDasharray="3 3" />
                                                <XAxis dataKey="hour" />
                                                <YAxis />
                                                <Tooltip />
                                                <Bar dataKey="count" fill="#82ca9d" />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </div>

                                    <div className="mb-6">
                                        <h5>Daily Activity</h5>
                                        <ResponsiveContainer width="100%" height={200}>
                                            <BarChart data={dailyData}>
                                                <CartesianGrid strokeDasharray="3 3" />
                                                <XAxis dataKey="day" />
                                                <YAxis />
                                                <Tooltip />
                                                <Bar dataKey="count" fill="#8884d8" />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </div>

                                    <div>
                                        <h5>Monthly Activity</h5>
                                        <ResponsiveContainer width="100%" height={200}>
                                            <BarChart data={monthlyData}>
                                                <CartesianGrid strokeDasharray="3 3" />
                                                <XAxis dataKey="month" />
                                                <YAxis />
                                                <Tooltip />
                                                <Bar dataKey="count" fill="#ffc658" />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>
                            ))}
                        </>
                    )}
                </div>
            )}

            {/* Timeline Tab */}
            {tab === "timeline" && timeline && (
                <div className="space-y-8">
                    {/* Overall Timeline */}
                    <div className="bg-white rounded shadow p-6">
                        <h3 className="text-xl font-semibold mb-4">Overall Messages Over Time</h3>
                        <ResponsiveContainer width="100%" height={300}>
                            <LineChart data={overallTimelineData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="date" angle={-45} textAnchor="end" height={60} />
                                <YAxis />
                                <Tooltip />
                                <Legend />
                                <Line type="monotone" dataKey="count" stroke="#8884d8" name="Messages" />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Per Person Timeline */}
                    {personsTimelineData.length > 0 && (
                        <>
                            <h3 className="text-2xl font-bold mt-10">Messages Over Time by Person</h3>
                            {personsTimelineData.map(({ person, data }) => (
                                <div key={person} className="bg-white rounded shadow p-6">
                                    <h4 className="text-lg font-semibold mb-4">{person}</h4>
                                    <ResponsiveContainer width="100%" height={250}>
                                        <LineChart data={data}>
                                            <CartesianGrid strokeDasharray="3 3" />
                                            <XAxis dataKey="date" angle={-45} textAnchor="end" height={60} />
                                            <YAxis />
                                            <Tooltip />
                                            <Legend />
                                            <Line type="monotone" dataKey="count" stroke="#82ca9d" name="Messages" />
                                        </LineChart>
                                    </ResponsiveContainer>
                                </div>
                            ))}
                        </>
                    )}
                </div>
            )}


            {/* Visualizations Tab */}
            {/* {tab === "visualizations" && visualizations && (
                <div>
                    {visualizations.weekday_chart && (
                        <img src={`data:image/png;base64,${visualizations.weekday_chart}`} alt="Weekday Chart" />
                    )}
                    {visualizations.month_chart && (
                        <img src={`data:image/png;base64,${visualizations.month_chart}`} alt="Month Chart" />
                    )}
                    {visualizations.timeline_chart && (
                        <img src={`data:image/png;base64,${visualizations.timeline_chart}`} alt="Timeline Chart" />
                    )}
                    {visualizations.pie_chart && (
                        <img src={`data:image/png;base64,${visualizations.pie_chart}`} alt="Pie Chart" />
                    )}
                    {visualizations.wordcloud && (
                        <img src={`data:image/png;base64,${visualizations.wordcloud}`} alt="Word Cloud" />
                    )}
                </div>
            )} */}
            {tab === "visualizations" && visualizations && (
                <div className="max-w-screen-md mx-auto">
                    {currentItems.map(item => (
                        <div key={item.key} className="mb-6">
                            <h4 className="font-semibold mb-2 text-center">{item.label}</h4>
                            <img
                                src={`data:image/png;base64,${item.data}`}
                                alt={item.label}
                                // className="mx-auto max-h-32 max-w-full object-contain rounded border shadow"
                                style={{ maxWidth: "800px", height: "auto" }}
                            />
                        </div>
                    ))}
                    <div className="flex justify-center items-center space-x-6 mt-4 px-2">
                        <button
                            onClick={() => setCurrentPage(p => Math.max(p - 1, 1))}
                            disabled={currentPage === 1}
                            className="px-4 py-2 bg-gray-200 rounded disabled:opacity-50 hover:bg-gray-300 transition"
                        >
                            Previous
                        </button>
                        <span className="text-sm font-medium">
                            Page {currentPage} of {totalPages}
                        </span>
                        <button
                            onClick={() => setCurrentPage(p => Math.min(p + 1, totalPages))}
                            disabled={currentPage === totalPages}
                            className="px-4 py-2 bg-gray-200 rounded disabled:opacity-50 hover:bg-gray-300 transition"
                        >
                            Next
                        </button>
                    </div>
                </div>
            )}



        </div>
    );
}

export default Dashboard;
