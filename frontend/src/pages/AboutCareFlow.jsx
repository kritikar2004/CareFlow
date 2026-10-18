import PageContainer from "../components/PageContainer";

function AboutCareFlow() {
  return (
    <PageContainer>
      <div className="about-page">
        <section className="about-hero">
          <div className="about-hero__content">
            <p className="page-eyebrow">ABOUT CAREFLOW</p>

            <h1>Hospital intelligence for better planning.</h1>

            <p className="about-hero__description">
              CareFlow is a hospital demand forecasting and disease
              intelligence platform designed to help hospitals make
              better operational decisions using data.
            </p>
          </div>
        </section>

        <section className="about-section">
          <div className="about-section__heading">
            <p className="page-eyebrow">WHAT CAREFLOW DOES</p>

            <h2>Turning data into operational insight.</h2>

            <p>
              CareFlow combines hospital data with forecasting and
              public disease and weather information to provide
              insights into expected demand, resource pressure, and
              disease trends.
            </p>
          </div>

          <div className="about-feature-grid">
            <article className="about-feature-card">
              <div className="about-feature-card__icon">▥</div>

              <h3>Hospital Demand Forecasting</h3>

              <p>
                Forecast expected hospital admissions and ICU demand
                to support advance planning.
              </p>
            </article>

            <article className="about-feature-card">
              <div className="about-feature-card__icon">◉</div>

              <h3>Disease Intelligence</h3>

              <p>
                Understand disease trends and forecast regional
                activity using available public data.
              </p>
            </article>

            <article className="about-feature-card">
              <div className="about-feature-card__icon">△</div>

              <h3>Resource Intelligence</h3>

              <p>
                Identify potential pressure on beds, ventilators,
                medicines, and other hospital resources.
              </p>
            </article>
          </div>
        </section>

        <section className="about-section about-contact">
          <div className="about-contact__content">
            <p className="page-eyebrow">CONTACT</p>

            <h2>Get in touch with the CareFlow team.</h2>

            <p>
              For questions, feedback, or information about the
              CareFlow project, contact us at:
            </p>

            <a
              href="mailto:careflowsupport1@gmail.com"
              className="about-contact__email"
            >
              careflowsupport1@gmail.com
            </a>
          </div>
        </section>

        <p className="about-disclaimer">
          CareFlow is a decision-support project. Forecasts are
          estimates based on historical and public data and should not
          be treated as clinical advice or as a substitute for
          professional healthcare decisions.
        </p>
      </div>
    </PageContainer>
  );
}

export default AboutCareFlow;