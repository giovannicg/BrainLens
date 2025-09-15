import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import { AuthProvider } from './contexts/AuthContext';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import ImageUpload from './pages/ImageUpload';
import Images from './pages/Images';
import ImageAnnotation from './pages/ImageAnnotation';
import Annotations from './pages/Annotations';
import Predictions from './pages/Predictions';
import PredictionResultsPage from './pages/PredictionResults';
import ImageChat from './pages/ImageChat';
import LoadingUpload from './pages/LoadingUpload';
import LoadingPredict from './pages/LoadingPredict';

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Navbar />
          <main className="main-content">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/upload" element={<ImageUpload />} />
              <Route path="/loading/upload" element={<LoadingUpload />} />
              <Route path="/loading/predict" element={<LoadingPredict />} />
              <Route path="/images" element={<Images />} />
              <Route path="/annotations" element={<Annotations />} />
              <Route path="/predictions" element={<Predictions />} />
              <Route path="/annotate/:imageId" element={<ImageAnnotation />} />
              <Route path="/prediction/:imageId" element={<PredictionResultsPage />} />
              <Route path="/chat/:imageId" element={<ImageChat />} />
            </Routes>
          </main>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
