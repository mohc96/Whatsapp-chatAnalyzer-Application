import React from "react";

function StatCard({ label, value }) {
    return (
        <div className="bg-white shadow rounded p-4 text-center">
            <div className="text-gray-500 text-sm">{label}</div>
            <div className="text-2xl font-bold text-blue-600">{value}</div>
        </div>
    );
}

export default StatCard;
