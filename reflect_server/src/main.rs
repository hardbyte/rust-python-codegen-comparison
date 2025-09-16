use axum::{response::Html, routing, Json};
use reflectapi::axum::into_router;
use std::{error::Error, sync::Arc};

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
    let app_state = Arc::new(reflect_server::AppState::default());

    // Use reflectapi routes directly
    let axum_app = into_router(app_state.clone(), routers, |_name, r| r)
        .route(
            "/openapi.json",
            routing::get(|| async { Json(openapi_spec) }),
        )
        .route(
            "/doc",
            routing::get(|| async { Html(include_str!("redoc.html")) }),
        );

    let port = std::env::var("PORT").unwrap_or_else(|_| "9000".to_string());
    let bind_addr = format!("0.0.0.0:{}", port);
    let listener = tokio::net::TcpListener::bind(&bind_addr).await?;
    eprintln!("ReflectAPI server listening on http://{}", bind_addr);
    eprintln!("Documentation UI (redoc): http://{}/doc", bind_addr);
    axum::serve(listener, axum_app).await?;

    Ok(())
}
