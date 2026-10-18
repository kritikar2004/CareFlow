import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import "./App.css";

import AuthLayout from "./layouts/AuthLayout";
import DashboardLayout from "./layouts/DashboardLayout";

import Login from "./pages/Login";
import SignUp from "./pages/SignUp";
import Dashboard from "./pages/Dashboard";
import HospitalDemand from "./pages/HospitalDemand";
import DiseaseIntelligence from "./pages/DiseaseIntelligence";
import BottleneckDetection from "./pages/BottleneckDetection";
import Profile from "./pages/Profile";
import AboutCareFlow from "./pages/AboutCareFlow";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AuthLayout />}>
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<SignUp />} />
        </Route>

        <Route element={<DashboardLayout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/hospital-demand" element={<HospitalDemand />} />
          <Route
            path="/disease-intelligence"
            element={<DiseaseIntelligence />}
          />
          <Route
            path="/bottleneck-detection"
            element={<BottleneckDetection />}
          />
          <Route path="/profile" element={<Profile />} />
          <Route path="/about" element={<AboutCareFlow />} />
        </Route>

        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;