# Scene2 Safety Rules

- Never modify, replace, delete, reserialize, or bulk-copy over `Assets/Scenes/Scene 2.unity` unless the user explicitly asks to change that exact scene file.
- Before modifying any scene asset, create a timestamped backup under `Backups/`.
- Never edit scene files while Unity is in Play Mode.
- Do not use another scene as a replacement for Scene2.
- When the user says Level02, do not modify Scene2 unless they explicitly name Scene2 too.
- Shared script changes that alter runtime behavior in Scene2 require a Scene2 backup first.
- Prefer small, targeted edits over whole-file replacement.
