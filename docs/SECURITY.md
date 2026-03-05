# JARVIS Security Guide

## Security Layers

1. **Input Validation** (`CommandValidator`) – blocks dangerous shell patterns
2. **Permission System** (`PermissionManager`) – controls what actions are allowed
3. **Sandbox** (`Sandbox`) – subprocess isolation with timeouts
4. **Confirmation** (`ConfirmationManager`) – requires approval for destructive actions
5. **Authentication** (`AuthManager`) – JWT token validation
6. **Encryption** (`EncryptionManager`) – Fernet symmetric encryption

## Blocked Command Patterns

- `rm -rf /` – recursive root delete
- `dd if=` – disk dump
- `mkfs` – filesystem format
- `shutdown`, `reboot`, `halt`
- `chmod 777`
- `sudo rm`

## Default Permissions

The following permissions are granted by default:

- `file.read`
- `network.access`
- `memory.read`
- `memory.write`

Actions requiring explicit grant:

- `file.write`, `file.delete`
- `browser.use`
- `system.exec`
- `agent.spawn`
- `admin`

## Production Checklist

- [ ] Set `JARVIS_SECRET_KEY` environment variable to a strong random value
- [ ] Set `require_auth: true` in `config/security.yaml`
- [ ] Enable HTTPS (TLS) on the API server
- [ ] Restrict CORS origins in `config/config.yaml`
- [ ] Review and restrict default permissions
- [ ] Enable sandboxing for all script execution
