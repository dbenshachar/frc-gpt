import * as vscode from 'vscode';
import fetch from 'node-fetch';

export function activate(context: vscode.ExtensionContext) {
    let timeout: NodeJS.Timer | undefined = undefined;
    let currentDecoration: vscode.TextEditorDecorationType | undefined = undefined;
    let lastCompletionText = "";

    const triggerDelay = 1000; // 1 second debounce

    // Decorations for ghost text (gray, italic)
    const createDecoration = () => vscode.window.createTextEditorDecorationType({
        opacity: '0.5',
        fontStyle: 'italic'
    });

    // This will store the position where the completion starts
    let completionStartPos: vscode.Position | undefined;

    // Register completion provider only for Java for example
    vscode.workspace.onDidChangeTextDocument(event => {
        if (timeout) {
            clearTimeout(timeout);
            timeout = undefined;
        }

        // Wait 1 second after typing stops
        timeout = setTimeout(async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) return;

            // Get all text before the cursor
            const position = editor.selection.active;
            const text = editor.document.getText(new vscode.Range(new vscode.Position(0, 0), position));

            // Call your autocomplete API
            try {
                const res = await fetch('http://127.0.0.1:8000/autocomplete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: text })
                });
                const data = await res.json();
                const completion = data.completion || "";

                // If empty or same as last, do nothing
                if (!completion || completion === lastCompletionText) return;
                lastCompletionText = completion;

                // Remove previous decoration if any
                if (currentDecoration) {
                    currentDecoration.dispose();
                    currentDecoration = undefined;
                }

                // Show ghost text decoration
                completionStartPos = editor.selection.active;
                const decoration = createDecoration();

                // Insert ghost text as decoration (virtual text)
                editor.setDecorations(decoration, [{
                    range: new vscode.Range(completionStartPos, completionStartPos),
                    renderOptions: {
                        after: {
                            contentText: completion,
                            color: 'gray',
                            fontStyle: 'italic'
                        }
                    }
                }]);
                currentDecoration = decoration;
            } catch (error) {
                console.error('Autocomplete fetch error:', error);
            }
        }, triggerDelay);
    });

    // Accept completion on Tab
    vscode.commands.registerCommand('extension.acceptCompletion', () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor || !completionStartPos || !lastCompletionText) return;

        editor.edit(editBuilder => {
            editBuilder.insert(completionStartPos!, lastCompletionText);
        });

        // Clear decoration and reset
        if (currentDecoration) {
            currentDecoration.dispose();
            currentDecoration = undefined;
        }
        lastCompletionText = "";
        completionStartPos = undefined;
    });

    // Bind tab key when decoration is active
    context.subscriptions.push(vscode.commands.registerCommand('type', async args => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) return;

        if (args.text === '\t' && lastCompletionText) {
            // If ghost text is showing, accept completion instead of inserting tab
            vscode.commands.executeCommand('extension.acceptCompletion');
        } else {
            await vscode.commands.executeCommand('default:type', args);
        }
    }));

    console.log('Autocomplete extension activated');
}

export function deactivate() {}
