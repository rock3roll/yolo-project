import React, { useState } from "react";
import { FaUpload, FaTrash, FaInfoCircle } from "react-icons/fa";
import "./App.css";

const App = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [showResult, setShowResult] = useState(false);
  const [imageUrl, setImageUrl] = useState(null);
  const [predictions, setPredictions] = useState([]);
  const [showFeedback, setShowFeedback] = useState(false);

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  const handleSubmit = async () => {
    if (selectedFile) {
      const formData = new FormData();
      formData.append("file", selectedFile);

      try {
        const response = await fetch("http://localhost:8000/upload/", {
          method: "POST",
          body: formData,
        });

        const data = await response.json();
        setImageUrl(data.image_url);
        setPredictions(data.predictions);
        setShowResult(true);
      } catch (error) {
        console.error("Error uploading image:", error);
      }
    }
  };

  const handleFeedbackSubmit = () => {
    alert("Submitted Successfully");
    setShowFeedback(false);
  };

  return (
    <div className="container">
      <header>
        <h1>Waste Classification Portal</h1>
      </header>
      {!showResult ? (
        <div className="home">
          <label className="file-upload">
            <input type="file" onChange={handleFileChange} />
            <FaUpload className="icon" /> Upload Image
          </label>
          <button className="submit-btn" onClick={handleSubmit}>
            Submit
          </button>
        </div>
      ) : (
        <div className="result">
          <h2>Detection Result</h2>
          {imageUrl && (
            <img
              src={`http://localhost:8000${imageUrl}`}
              alt="Uploaded"
              className="uploaded-image"
            />
          )}
          <table>
            <thead>
              <tr>
                <th>S.No</th>
                <th>Class</th>
                <th>Recyclable</th>
                <th>Dry/Wet</th>
                <th>Disposal Info</th>
              </tr>
            </thead>
            <tbody>
              {predictions.map((pred, index) => (
                <tr key={index}>
                  <td>{index + 1}</td>
                  <td>{pred.class}</td>
                  <td>{pred.recyclable}</td>
                  <td>{pred.dry_wet}</td>
                  <td>{pred.disposal_info}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <button
            className="feedback-btn"
            onClick={() => setShowFeedback(true)}
          >
            Feedback
          </button>
          {showFeedback && (
            <div className="feedback-modal">
              <h3>Provide Feedback</h3>
              <label>Class Name:</label>
              <input type="text" />
              <label>Actual Prediction:</label>
              <input type="text" />
              <label>Model Prediction:</label>
              <input type="text" />
              <button className="submit-btn" onClick={handleFeedbackSubmit}>
                Submit
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default App;
