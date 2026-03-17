#!/bin/bash
# ============================================================
# install_macos.sh — Cài đặt Right-click Context Menu trên macOS
# Thêm "Chuyển MD sang DOCX" vào menu chuột phải cho file .md
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_NAME="Chuyển MD sang DOCX"
WORKFLOW_DIR="$HOME/Library/Services/${SERVICE_NAME}.workflow"

echo ""
echo "============================================================"
echo "  md2docx — Cài đặt Right-click Menu (macOS)"
echo "============================================================"
echo ""

# Kiểm tra md2docx có trong PATH không
if ! command -v md2docx &>/dev/null; then
    echo "⚠️  'md2docx' chưa có trong PATH."
    echo "   Đang thêm $SCRIPT_DIR vào PATH..."
    
    SHELL_RC="$HOME/.zshrc"
    if [[ "$SHELL" == *"bash"* ]]; then
        SHELL_RC="$HOME/.bashrc"
    fi
    
    if ! grep -q "$SCRIPT_DIR" "$SHELL_RC" 2>/dev/null; then
        echo "export PATH=\"$SCRIPT_DIR:\$PATH\"" >> "$SHELL_RC"
        echo "   ✅ Đã thêm vào $SHELL_RC"
    else
        echo "   ✅ Đã có trong $SHELL_RC"
    fi
    export PATH="$SCRIPT_DIR:$PATH"
fi

# Xóa workflow cũ nếu có
rm -rf "$WORKFLOW_DIR"

# Tạo Automator Quick Action
echo "[1/2] 📦 Tạo Quick Action..."

mkdir -p "$WORKFLOW_DIR/Contents"

# === Info.plist ===
cat > "$WORKFLOW_DIR/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>CFBundleName</key>
	<string>Chuyển MD sang DOCX</string>
	<key>CFBundleIdentifier</key>
	<string>com.setcom.md2docx.quickaction</string>
	<key>NSServices</key>
	<array>
		<dict>
			<key>NSMenuItem</key>
			<dict>
				<key>default</key>
				<string>Chuyển MD sang DOCX</string>
			</dict>
			<key>NSMessage</key>
			<string>runWorkflowAsService</string>
			<key>NSSendFileTypes</key>
			<array>
				<string>net.daringfireball.markdown</string>
				<string>public.plain-text</string>
				<string>public.data</string>
			</array>
		</dict>
	</array>
</dict>
</plist>
EOF

# Shell command (escaped for plist)
SHELL_CMD="export PATH=\"${SCRIPT_DIR}:\$PATH\"
for f in \"\$@\"; do
    if [[ \"\$f\" == *.md ]] || [[ \"\$f\" == *.markdown ]]; then
        \"${SCRIPT_DIR}/md2docx\" \"\$f\" 2>&amp;1
        docx=\"\${f%.md}.docx\"
        osascript -e \"display notification \\\\\"Đã tạo: \$(basename \\\\\"\$docx\\\\\")\\\\\" with title \\\\\"md2docx\\\\\" sound name \\\\\"Glass\\\\\"\" 2>/dev/null
    fi
done"

# === document.wflow ===
cat > "$WORKFLOW_DIR/Contents/document.wflow" << ENDWFLOW
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>AMApplicationBuild</key>
	<string>523</string>
	<key>AMApplicationVersion</key>
	<string>2.10</string>
	<key>AMDocumentVersion</key>
	<string>2</string>
	<key>actions</key>
	<array>
		<dict>
			<key>action</key>
			<dict>
				<key>AMAccepts</key>
				<dict>
					<key>Container</key>
					<string>List</string>
					<key>Optional</key>
					<false/>
					<key>Types</key>
					<array>
						<string>com.apple.cocoa.path</string>
					</array>
				</dict>
				<key>AMActionVersion</key>
				<string>1.0.2</string>
				<key>AMApplication</key>
				<array>
					<string>Automator</string>
				</array>
				<key>AMBundleIdentifier</key>
				<string>com.apple.RunShellScript</string>
				<key>AMCategory</key>
				<array>
					<string>AMCategoryUtilities</string>
				</array>
				<key>AMIconName</key>
				<string>com.apple.RunShellScript</string>
				<key>AMParameterProperties</key>
				<dict>
					<key>COMMAND_STRING</key>
					<dict/>
					<key>CheckedForUserDefaultShell</key>
					<dict/>
					<key>inputMethod</key>
					<dict/>
					<key>shell</key>
					<dict/>
					<key>source</key>
					<dict/>
				</dict>
				<key>AMProvides</key>
				<dict>
					<key>Container</key>
					<string>List</string>
					<key>Types</key>
					<array>
						<string>com.apple.cocoa.path</string>
					</array>
				</dict>
				<key>ActionBundlePath</key>
				<string>/System/Library/Automator/Run Shell Script.action</string>
				<key>ActionName</key>
				<string>Run Shell Script</string>
				<key>ActionParameters</key>
				<dict>
					<key>COMMAND_STRING</key>
					<string>${SHELL_CMD}</string>
					<key>CheckedForUserDefaultShell</key>
					<true/>
					<key>inputMethod</key>
					<integer>1</integer>
					<key>shell</key>
					<string>/bin/zsh</string>
					<key>source</key>
					<string></string>
				</dict>
				<key>BundleIdentifier</key>
				<string>com.apple.RunShellScript</string>
				<key>CFBundleVersion</key>
				<string>1.0.2</string>
				<key>CanShowSelectedItemsWhenRun</key>
				<false/>
				<key>CanShowWhenRun</key>
				<true/>
				<key>Category</key>
				<array>
					<string>AMCategoryUtilities</string>
				</array>
				<key>Class Name</key>
				<string>RunShellScriptAction</string>
				<key>InputUUID</key>
				<string>A7B3C4D5-E6F7-4A8B-9C0D-E1F2A3B4C5D6</string>
				<key>Keywords</key>
				<array>
					<string>Shell</string>
					<string>Script</string>
				</array>
				<key>OutputUUID</key>
				<string>B8C4D5E6-F7A8-4B9C-0D1E-F2A3B4C5D6E7</string>
				<key>UUID</key>
				<string>C9D5E6F7-A8B9-4C0D-1E2F-A3B4C5D6E7F8</string>
				<key>UnlocalizedApplications</key>
				<array>
					<string>Automator</string>
				</array>
				<key>arguments</key>
				<dict>
					<key>0</key>
					<dict>
						<key>default value</key>
						<integer>0</integer>
						<key>name</key>
						<string>inputMethod</string>
						<key>required</key>
						<string>0</string>
						<key>type</key>
						<string>0</string>
						<key>uuid</key>
						<string>0</string>
					</dict>
				</dict>
			</dict>
		</dict>
	</array>
	<key>connectors</key>
	<dict/>
	<key>workflowMetaData</key>
	<dict>
		<key>applicationBundleIDsByPath</key>
		<dict/>
		<key>applicationPaths</key>
		<array/>
		<key>inputTypeIdentifier</key>
		<string>com.apple.Automator.fileSystemObject</string>
		<key>outputTypeIdentifier</key>
		<string>com.apple.Automator.nothing</string>
		<key>presentationMode</key>
		<integer>15</integer>
		<key>processesInput</key>
		<integer>0</integer>
		<key>serviceApplicationBundleID</key>
		<string>com.apple.finder</string>
		<key>serviceApplicationPath</key>
		<string>/System/Applications/Finder.app</string>
		<key>serviceInputTypeIdentifier</key>
		<string>com.apple.Automator.fileSystemObject</string>
		<key>serviceOutputTypeIdentifier</key>
		<string>com.apple.Automator.nothing</string>
		<key>serviceProcessesInput</key>
		<integer>0</integer>
		<key>systemImageName</key>
		<string>NSActionTemplate</string>
		<key>useAutomaticInputType</key>
		<integer>0</integer>
		<key>workflowTypeIdentifier</key>
		<string>com.apple.Automator.servicesMenu</string>
	</dict>
</dict>
</plist>
ENDWFLOW

echo "   ✅ Quick Action tạo tại: $WORKFLOW_DIR"

# Refresh Services + rebuild LaunchServices
echo "[2/2] 🔄 Refresh Services..."
/System/Library/CoreServices/pbs -flush 2>/dev/null || true
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -kill -r -domain local -domain system -domain user 2>/dev/null || true

echo ""
echo "============================================================"
echo "  ✅ CÀI ĐẶT HOÀN TẤT!"
echo ""
echo "  Cách dùng:"
echo "  1. Click phải vào file .md trong Finder"
echo "  2. Chọn: Quick Actions → \"Chuyển MD sang DOCX\""
echo "  3. File .docx sẽ được tạo tại cùng thư mục"
echo ""
echo "  💡 Nếu không thấy menu ngay, thử:"
echo "     - Đóng và mở lại Finder (Cmd+Q Finder)"
echo "     - Hoặc restart máy"
echo "     - System Settings → Privacy & Security → Extensions"
echo "       → Finder → bật \"Chuyển MD sang DOCX\""
echo "============================================================"
echo ""
