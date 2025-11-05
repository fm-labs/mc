import React from "react";

const ActiveSessions = () => {

    const activeSessions = [
        {
            id: 1,
            device: "Chrome on Windows",
            location: "New York, USA",
            ipAddress: "12.3.4.5"
        }
    ];


    return (
        <div>
            {activeSessions.length === 0 ? (
                <p>No active sessions found.</p>
            ) : (
                <table className="w-full table-auto border-collapse border border-gray-300">
                    <thead>
                    <tr>
                        <th className="border border-gray-300 px-4 py-2 text-left">Device</th>
                        <th className="border border-gray-300 px-4 py-2 text-left">Location</th>
                        <th className="border border-gray-300 px-4 py-2 text-left">IP Address</th>
                    </tr>
                    </thead>
                    <tbody>
                    {activeSessions.map((session) => (
                        <tr key={session.id} className="hover:bg-gray-100">
                            <td className="border border-gray-300 px-4 py-2">{session.device}</td>
                            <td className="border border-gray-300 px-4 py-2">{session.location}</td>
                            <td className="border border-gray-300 px-4 py-2">{session.ipAddress}</td>
                        </tr>
                    ))}
                    </tbody>
                </table>
            )}
        </div>
    );
};

export default ActiveSessions;
