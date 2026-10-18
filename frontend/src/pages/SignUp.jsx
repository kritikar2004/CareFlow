import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { registerUser } from "../api/auth";

function SignUp() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    hospitalName: "",
    phone: "",
    email: "",
    city: "",
    password: "",
  });

  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData((previous) => ({
      ...previous,
      [name]: value,
    }));

    if (error) {
      setError("");
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setIsSubmitting(true);

    try {
      await registerUser({
        hospital_name: formData.hospitalName,
        phone: formData.phone,
        email: formData.email,
        password: formData.password,
        city: formData.city,
      });

      navigate("/login");
    } catch (requestError) {
      const detail = requestError.response?.data?.detail;

      setError(
        typeof detail === "string"
          ? detail
          : "Unable to create the account. Please check your details and try again."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-page__content">
        <div className="auth-page__heading">
          <span className="auth-page__eyebrow">
            Hospital Registration
          </span>

          <h1>Create your CareFlow account</h1>

          <p>
            Register your hospital to access demand forecasting and operational
            intelligence.
          </p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="form-field">
            <label htmlFor="hospitalName">Hospital name</label>

            <input
              id="hospitalName"
              name="hospitalName"
              type="text"
              placeholder="Enter hospital name"
              autoComplete="organization"
              value={formData.hospitalName}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-field">
            <label htmlFor="phone">Phone number</label>

            <input
              id="phone"
              name="phone"
              type="tel"
              placeholder="Enter hospital phone number"
              autoComplete="tel"
              value={formData.phone}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-field">
            <label htmlFor="email">Email address</label>

            <input
              id="email"
              name="email"
              type="email"
              placeholder="hospital@example.com"
              autoComplete="email"
              value={formData.email}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-field">
            <label htmlFor="city">Location</label>

            <input
              id="city"
              name="city"
              type="text"
              placeholder="Enter city"
              autoComplete="address-level2"
              value={formData.city}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-field">
            <label htmlFor="password">Password</label>

            <input
              id="password"
              name="password"
              type="password"
              placeholder="Create a password"
              autoComplete="new-password"
              value={formData.password}
              onChange={handleChange}
              required
            />
          </div>

          {error && (
            <p className="auth-form__error" role="alert">
              {error}
            </p>
          )}

          <button
            type="submit"
            className="button button--primary button--full"
            disabled={isSubmitting}
          >
            {isSubmitting
              ? "Creating account..."
              : "Create hospital account"}
          </button>
        </form>

        <div className="auth-page__footer">
          <span>Already have a CareFlow account?</span>

          <Link to="/login" className="form-link">
            Sign in
          </Link>
        </div>

        <p className="auth-page__disclaimer">
          CareFlow provides operational forecasts and decision-support
          information. It does not provide diagnosis or treatment advice.
        </p>
      </div>
    </div>
  );
}

export default SignUp;