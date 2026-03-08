use tauri::Manager;
use tauri_plugin_shell::ShellExt;

/// Parse the PORT:{port} line from sidecar stdout.
fn parse_port(line: &str) -> Option<u16> {
    line.trim()
        .strip_prefix("PORT:")
        .and_then(|s| s.parse::<u16>().ok())
}

/// Poll the server health endpoint until it responds 200.
async fn wait_for_server(port: u16, timeout_secs: u64) -> Result<(), String> {
    let url = format!("http://127.0.0.1:{}/api/docs", port);
    let client = reqwest::Client::new();
    let deadline = std::time::Instant::now() + std::time::Duration::from_secs(timeout_secs);

    while std::time::Instant::now() < deadline {
        if let Ok(resp) = client.get(&url).send().await {
            if resp.status().is_success() {
                return Ok(());
            }
        }
        tokio::time::sleep(std::time::Duration::from_millis(250)).await;
    }

    Err(format!(
        "Server did not become ready within {}s",
        timeout_secs
    ))
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_notification::init())
        .setup(|app| {
            let app_handle = app.handle().clone();

            // Spawn sidecar startup in background
            tauri::async_runtime::spawn(async move {
                let shell = app_handle.shell();

                let (mut rx, _child) = match shell.sidecar("binaries/foundrai-server") {
                    Ok(cmd) => match cmd.spawn() {
                        Ok(result) => result,
                        Err(e) => {
                            eprintln!("Failed to spawn sidecar: {}", e);
                            show_error(&app_handle, &format!("Failed to start server: {}", e));
                            return;
                        }
                    },
                    Err(e) => {
                        eprintln!("Failed to create sidecar command: {}", e);
                        show_error(&app_handle, &format!("Server binary not found: {}", e));
                        return;
                    }
                };

                // Read stdout to find the port
                let mut port: Option<u16> = None;
                let deadline =
                    std::time::Instant::now() + std::time::Duration::from_secs(15);

                while std::time::Instant::now() < deadline {
                    match tokio::time::timeout(
                        std::time::Duration::from_secs(1),
                        rx.recv(),
                    )
                    .await
                    {
                        Ok(Some(event)) => {
                            if let tauri_plugin_shell::process::CommandEvent::Stdout(line) = event {
                                let line_str = String::from_utf8_lossy(&line);
                                if let Some(p) = parse_port(&line_str) {
                                    port = Some(p);
                                    break;
                                }
                            }
                        }
                        Ok(None) => {
                            // Channel closed — sidecar exited
                            show_error(&app_handle, "Server process exited unexpectedly.");
                            return;
                        }
                        Err(_) => {
                            // Timeout on this read, keep trying
                            continue;
                        }
                    }
                }

                let port = match port {
                    Some(p) => p,
                    None => {
                        show_error(&app_handle, "Could not determine server port. The server may have failed to start.");
                        return;
                    }
                };

                // Wait for server to be ready
                if let Err(e) = wait_for_server(port, 30).await {
                    show_error(&app_handle, &format!("Server startup failed: {}", e));
                    return;
                }

                // Navigate main window to server URL
                let url = format!("http://127.0.0.1:{}", port);
                if let Some(window) = app_handle.get_webview_window("main") {
                    let _ = window.navigate(url.parse().unwrap());
                    let _ = window.show();
                }
            });

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

fn show_error(app: &tauri::AppHandle, message: &str) {
    eprintln!("FoundrAI Error: {}", message);
    // Show the main window with an error message
    if let Some(window) = app.get_webview_window("main") {
        let html = format!(
            r#"data:text/html,<html><body style="font-family:system-ui;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;background:%23111;color:%23fff"><div style="text-align:center"><h1>FoundrAI</h1><p style="color:%23f87171">{}</p><p style="color:%23999">Check the logs or restart the application.</p></div></body></html>"#,
            message
        );
        let _ = window.navigate(html.parse().unwrap());
        let _ = window.show();
    }
}
