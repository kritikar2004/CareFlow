import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { loginUser } from "../api/auth";

function Login() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    email: "",
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
      await loginUser(formData);
      navigate("/dashboard");
    } catch (requestError) {
      const detail = requestError.response?.data?.detail;

      setError(
        typeof detail === "string"
          ? detail
          : "Unable to sign in. Please check your credentials and try again."
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
            Hospital Intelligence Platform
          </span>

          <h1>Welcome back</h1>

          <p>
            Sign in to access your hospital demand forecasts and operational
            intelligence.
          </p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
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
            <div className="form-field__label-row">
              <label htmlFor="password">Password</label>

              <button type="button" className="form-link">
                Forgot password?
              </button>
            </div>

            <input
              id="password"
              name="password"
              type="password"
              placeholder="Enter your password"
              autoComplete="current-password"
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
            {isSubmitting ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <div className="auth-page__footer">
          <span>Don't have a CareFlow account?</span>

          <Link to="/signup" className="form-link">
            Create hospital account
          </Link>
        </div>

        <p className="auth-page__disclaimer">
          Forecasts are estimates based on historical and public data. They
          should not be treated as clinical advice or as a substitute for
          professional healthcare decisions.
        </p>
      </div>
    </div>
  );
}

export default Login;