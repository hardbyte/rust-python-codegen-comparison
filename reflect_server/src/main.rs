use std::error::Error;
use axum::{response::Html, Json};

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    let builder = reflect_server::builder();
    let (schema, routers) = builder.build()?;
    let openapi_spec = reflectapi::codegen::openapi::Spec::from(&schema);

    // Write reflect schema to a file
    tokio::fs::write(
        format!("{}/{}", env!("CARGO_MANIFEST_DIR"), "reflectapi.json"),
        serde_json::to_string_pretty(&schema).unwrap(),
    )
    .await?;

    // Start the server based on axum web framework
    let app_state = Default::default();
    let axum_app = reflectapi::into_router(app_state, routers, |_name, r| r)
        .route(
            "/openapi.json",
            axum::routing::get(|| async { Json(openapi_spec) }),
        )
        .route(
            "/swagger-ui",
            axum::routing::get(|| async {
                Html(r#"
<!DOCTYPE html>
<html>
<head>
    <title>API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3.25.0/swagger-ui.css" />
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@3.25.0/swagger-ui-bundle.js"></script>
    <script>
        SwaggerUIBundle({
            url: '/openapi.json',
            dom_id: '#swagger-ui',
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIBundle.presets.standalone
            ]
        });
    </script>
</body>
</html>
                "#)
            }),
        );

    let port = std::env::var("PORT").unwrap_or_else(|_| "9000".to_string());
    let bind_addr = format!("0.0.0.0:{}", port);
    let listener = tokio::net::TcpListener::bind(&bind_addr).await?;
    eprintln!("ReflectAPI server listening on http://{}", bind_addr);
    eprintln!("Swagger UI: http://{}/swagger-ui", bind_addr);
    axum::serve(listener, axum_app).await?;

    Ok(())
}
