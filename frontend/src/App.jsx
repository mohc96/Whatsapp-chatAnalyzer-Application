import React, { useState } from "react";
import UploadForm from "./components/UploadForm";
import Dashboard from "./pages/Dashboard";

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [filename, setFilename] = useState(null);

  const handleSessionCreated = (sid, fname) => {
    setSessionId(sid);
    setFilename(fname);
  };

  return (
    <div>
      <h1 className="text-3xl font-bold text-center my-8">WhatsApp Analyzer</h1>
      {!sessionId ? (
        <UploadForm onSessionCreated={handleSessionCreated} />
      ) : (
        <Dashboard sessionId={sessionId} sessionFilename={filename} />
      )}
    </div>
  );
}

export default App;
