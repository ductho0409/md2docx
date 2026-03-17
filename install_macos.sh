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

# Tạo Automator Quick Action
echo "[1/2] 📦 Tạo Quick Action..."

rm -rf "$WORKFLOW_DIR"
mkdir -p "$WORKFLOW_DIR/Contents"

# Info.plist
cat > "$WORKFLOW_DIR/Contents/Info.plist" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
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
        </dict>
    </array>
</dict>
</plist>
PLIST

# document.wflow
cat > "$WORKFLOW_DIR/Contents/document.wflow" << WFLOW
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
				<key>AMKeywords</key>
				<array>
					<string>Shell</string>
					<string>Script</string>
					<string>Command</string>
					<string>Run</string>
					<string>Unix</string>
				</array>
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
				<key>AMRequiredResources</key>
				<array/>
				<key>ActionBundlePath</key>
				<string>/System/Library/Automator/Run Shell Script.action</string>
				<key>ActionName</key>
				<string>Run Shell Script</string>
				<key>ActionParameters</key>
				<dict>
					<key>COMMAND_STRING</key>
					<string>export PATH="$SCRIPT_DIR:\$PATH"

for f in "\$@"; do
    if [[ "\$f" == *.md ]]; then
        "$SCRIPT_DIR/md2docx" "\$f"
        
        # Thông báo hoàn tất
        docx="\${f%.md}.docx"
        osascript -e "display notification \"Đã tạo: \$(basename \"\$docx\")\" with title \"md2docx\" sound name \"Glass\""
    fi
done</string>
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
				<string>A1234567-B123-C123-D123-E12345678901</string>
				<key>Keywords</key>
				<array>
					<string>Shell</string>
					<string>Script</string>
					<string>Command</string>
					<string>Run</string>
					<string>Unix</string>
				</array>
				<key>OutputUUID</key>
				<string>F1234567-B123-C123-D123-E12345678902</string>
				<key>UUID</key>
				<string>01234567-B123-C123-D123-E12345678903</string>
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
		<key>workflowTypeIdentifier</key>
		<string>com.apple.Automator.servicesMenu</string>
	</dict>
</dict>
</plist>
WFLOW

echo "   ✅ Quick Action tạo tại: $WORKFLOW_DIR"

# Refresh Services
echo "[2/2] 🔄 Refresh Services cache..."
/System/Library/CoreServices/pbs -flush 2>/dev/null || true

echo ""
echo "============================================================"
echo "  ✅ CÀI ĐẶT HOÀN TẤT!"
echo ""
echo "  Cách dùng:"
echo "  1. Click phải vào file .md trong Finder"
echo "  2. Chọn: Quick Actions → \"Chuyển MD sang DOCX\""
echo "  3. File .docx sẽ được tạo tại cùng thư mục"
echo ""
echo "  💡 Nếu không thấy menu, vào:"
echo "     System Settings → Privacy & Security → Extensions"
echo "     → Finder Extensions → bật \"Chuyển MD sang DOCX\""
echo "============================================================"
echo ""
