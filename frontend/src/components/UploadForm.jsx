// import React, { useState } from "react";
// import { uploadChatFile } from "../api/whatsapp";

// function UploadForm({ onSessionCreated }) {
//     const [file, setFile] = useState();
//     const [loading, setLoading] = useState(false);
//     const [error, setError] = useState();

//     const handleFile = (e) => setFile(e.target.files[0]);
//     const handleUpload = async (e) => {
//         e.preventDefault();
//         setLoading(true);
//         setError(null);
//         const formData = new FormData();
//         formData.append("file", file);
//         try {
//             const res = await uploadChatFile(formData);
//             onSessionCreated(res.session_id, res.filename);
//         } catch (e) {
//             setError(e.response?.data?.detail || "Upload failed");
//         }
//         setLoading(false);
//     };

//     return (
//         <form onSubmit={handleUpload} className="bg-white p-6 rounded shadow w-full md:w-1/2 mx-auto">
//             <label className="block text-lg mb-2">Upload WhatsApp Chat (.txt)</label>
//             <br></br>
//             <p>
//                 Please upload your exported WhatsApp chat text file (.txt) below.
//                 The app will analyze your chat and provide detailed insights.
//             </p>
//             <input type="file" accept=".txt" onChange={handleFile} required className="mb-3" />
//             <br></br>
//             {error && <p className="text-red-600">{error}</p>}
//             <br></br>
//             <button type="submit" className="bg-blue-600 text-white px-6 py-2 rounded"
//                 disabled={!file || loading}>
//                 {loading ? "Uploading..." : "Analyze"}
//             </button>
//         </form>
//     );
// }
// export default UploadForm;


import React, { useState } from "react";
import { uploadChatFile } from "../api/whatsapp";

function UploadForm({ onSessionCreated }) {
    const [file, setFile] = useState();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState();

    const handleFile = (e) => setFile(e.target.files[0]);
    const handleUpload = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        const formData = new FormData();
        formData.append("file", file);
        try {
            const res = await uploadChatFile(formData);
            onSessionCreated(res.session_id, res.filename);
        } catch (e) {
            setError(e.response?.data?.detail || "Upload failed");
        }
        setLoading(false);
    };

    return (
        <form
            onSubmit={handleUpload}
            className="bg-white p-6 rounded shadow w-full md:w-1/2 mx-auto"
        >
            <label className="block text-lg mb-2">Upload WhatsApp Chat (.txt)</label>

            <p className="mb-4 text-gray-700">
                Please upload your exported WhatsApp chat text file (.txt) below.
                The app will analyze your chat and provide detailed insights.
            </p>

            <input
                type="file"
                accept=".txt"
                onChange={handleFile}
                required
                className="mb-4"
            />

            {error && <p className="text-red-600 mb-4">{error}</p>}

            <button
                type="submit"
                className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 transition"
                disabled={!file || loading}
            >
                {loading ? "Uploading..." : "Analyze"}
            </button>
        </form>
    );
}

export default UploadForm;
