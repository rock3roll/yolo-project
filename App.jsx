import React, { useState } from "react";
import { FaUpload, FaTrash, FaInfoCircle } from "react-icons/fa";
import "./App.css";
import axios from "axios";
//import "bootstrap/dist/css/bootstrap.min.css";
const App = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [showResult, setShowResult] = useState(false);
  const [imageUrl, setImageUrl] = useState(null);
  const [predictions, setPredictions] = useState([]);
  const [showFeedback, setShowFeedback] = useState(false);
  const [previewUrl, setPreview] = useState(null);
  const [feedbackData, setFeedbackData] = useState({
    s_no: 0,
    actual_class: "",
    predicted_class: "",
  });
  const [popupInfo, setPopupInfo] = useState(null);
  const [admin, setAdmin] = useState(false);
  const [className, setClassName] = useState("");
  const [result, setResult] = useState("");
  const [selectedFileName, setSelectedFileName] = useState("");

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
    setSelectedFileName(event.target.files[0].name);
    setPreview(URL.createObjectURL(event.target.files[0]));
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
        setClassName(data.class);
        setShowResult(true);
        setFeedbackData({ s_no: 0, actual_class: "", predicted_class: "" });
      } catch (error) {
        console.error("Error uploading image:", error);
      }
    }
  };

  /* const handleFeedbackSubmit = async (detectionid) => {
    const sel_pred = predictions.find((pred) => pred.s_no == detectionid);
    if (!sel_pred) {
      alert("Invalid Detection ID!");
      return;
    }

    const feedbackData = {
      s_no: sel_pred.s_no, // Detection ID
      class: sel_pred.class, // Predicted Class
      bounding_box: sel_pred.bounding_box, // Bounding Box Coordinates
    };

    //alert("Submitted Successfully");
    //setShowFeedback(false);

    try {
      const response = await fetch("http://localhost:8000/submit-feedback/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(feedbackData),
      });

      if (response.ok) {
        alert("Feedback Submitted Successfully!");
        setShowFeedback(false);
      } else {
        alert("Failed to submit feedback");
      }
    } catch (error) {
      console.error("Error submitting feedback:", error);
    }
  };*/

  const handleFeedbackSubmit = async (e) => {
    e.preventDefault();

    try {
      const response = await axios.post(
        "http://localhost:8000/submit-feedback/",
        feedbackData
      );
      alert("success");
      setShowFeedback(false);
    } catch (error) {
      console.error("Error submitting feedback:", error);
    }
  };

  const handleFeedbackChange = (e) => {
    setFeedbackData({ ...feedbackData, [e.target.name]: e.target.value });
  };

  const handleViewInfo = (info) => {
    setPopupInfo(info);
  };

  const closePopup = () => {
    setPopupInfo(null);
  };
  const closeFeedback = () => setShowFeedback(false);

  const handleDispSubmit = async (class_) => {
    console.log(className);
    try {
      const res = await axios.post(
        "http://localhost:8000/generate-disposal-info/",
        {
          class_name: class_,
        }
      );

      setPopupInfo(res.data.disposal_info);
    } catch (error) {
      setResult("Error: " + error.response?.data?.detail || "Unknown error");
    }
  };

  return (
    <>
      <div className="header">
        <h1 className="header-title">
          Waste Detection and Classification Portal
        </h1>
        <button className="header-button" onClick={() => setAdmin(true)}>
          Admin
        </button>
      </div>
      {!showResult && !admin ? (
        <div className="home">
          <label className="file-upload">
            <input type="file" onChange={handleFileChange} />
            <FaUpload className="icon" /> Upload Image
          </label>
          {selectedFileName && (
            <p className="file-name">
              Selected file: <strong>{selectedFileName}</strong>
            </p>
          )}
          <button className="submit-btn" onClick={handleSubmit}>
            Submit
          </button>
        </div>
      ) : (
        <div className="result">
          <h2>Detection Result</h2>
          {imageUrl && (
            <div style={{ display: "flex", flexDirection: "row", gap: "30px" }}>
              <img src={previewUrl} alt="Preview" className="uploaded-image" />
              <img
                src={`http://localhost:8000${imageUrl}`}
                alt="Uploaded"
                className="uploaded-image"
              />
            </div>
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
                  <td>{pred.s_no}</td>
                  <td>{pred.class}</td>
                  <td>{pred.recyclable}</td>
                  <td>{pred.dry_wet}</td>

                  <td>
                    {/*} <button style = {{backgroundColor: '#0d6efd'}} onClick={() => handleViewInfo(pred.disposal_info)}>
                                    View Info
                 </button>*/}
                    <button
                      style={{ backgroundColor: "#0d6efd" }}
                      onClick={() => handleDispSubmit(pred.class)}
                    >
                      View Info
                    </button>
                  </td>

                  {/*} 
                <td>{pred.disposal_info}</td>
                <td>
                 <button onClick={() => handleViewInfo(pred.disposal_info)} className="btn btn-primary">
                                    View Info
                 </button>
                    </td>*/}
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ display: "flex", flexDirection: "row", gap: "30px" }}>
            <button
              className="feedback-btn"
              onClick={() => setShowFeedback(true)}
            >
              Feedback
            </button>
            <button
              className="feedback-btn"
              onClick={() => {
                setShowResult(false);
                setSelectedFileName("");
              }}
            >
              Back
            </button>
          </div>
          {showFeedback && (
            <div className="feedback-modal">
              <h3>Provide Feedback</h3>
              <button className="close-btn" onClick={closeFeedback}>
                ✖
              </button>
              <label>Detection ID: </label>
              <input
                name="s_no"
                type="text"
                value={feedbackData.s_no}
                onChange={handleFeedbackChange}
              />
              <label>Actual Prediction:</label>
              <input
                name="actual_class"
                type="text"
                value={feedbackData.actual_class}
                onChange={handleFeedbackChange}
              />
              <label>Model Prediction:</label>
              <input
                name="model_class"
                type="text"
                value={feedbackData.predicted_class_}
                onChange={handleFeedbackChange}
              />

              <button className="submit-btn" onClick={handleFeedbackSubmit}>
                Submit
              </button>
            </div>
          )}

          {popupInfo && (
            <div
              className="feedback-modal"
              style={{ width: "600px", textAlign: "justify" }}
            >
              <button className="close-btn" onClick={closePopup}>
                ✖
              </button>
              <h3 style={{ textAlign: "center" }}>Disposal Information</h3>
              <p style={{ color: "black" }}>{popupInfo}</p>
            </div>
          )}
        </div>
      )}
    </>
  );
};

export default App;
