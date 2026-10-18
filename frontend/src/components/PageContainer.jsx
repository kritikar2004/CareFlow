function PageContainer({
  eyebrow,
  title,
  description,
  actions,
  children,
  className = "",
}) {
  return (
    <div className={`page-container ${className}`.trim()}>
      {(eyebrow || title || description || actions) && (
        <div className="page-header">
          <div className="page-header__content">
            {eyebrow && (
              <div className="page-header__eyebrow">{eyebrow}</div>
            )}

            {title && <h1 className="page-header__title">{title}</h1>}

            {description && (
              <p className="page-header__description">{description}</p>
            )}
          </div>

          {actions && <div className="page-header__actions">{actions}</div>}
        </div>
      )}

      {children}
    </div>
  );
}

export default PageContainer;