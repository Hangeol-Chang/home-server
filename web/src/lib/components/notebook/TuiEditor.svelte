<script>
	import { onMount, onDestroy } from 'svelte';
	import '@toast-ui/editor/dist/toastui-editor.css';
    // Dark mode support if needed, but let's stick to default first
    // import '@toast-ui/editor/dist/theme/toastui-editor-dark.css';

	let { 
        value = $bindable(''), 
        height = '100%',
        previewStyle = 'vertical',
        initialEditType = 'markdown',
        viewer = false
    } = $props();

	let editorDiv;
	let instance;

	onMount(async () => {
        // Dynamic import to avoid SSR issues
		const module = await import('@toast-ui/editor');
        const Editor = module.Editor; // or module.default depending on export

		instance = new Editor({
			el: editorDiv,
			initialEditType: initialEditType,
			previewStyle: previewStyle,
			height: height,
			initialValue: value,
            usageStatistics: false,
            viewer: viewer,
			events: {
				change: () => {
                    if (!viewer) {
					    value = instance.getMarkdown();
                    }
				}
			}
		});
	});

	onDestroy(() => {
		instance?.destroy();
	});
    
    // Handle external value updates (e.g. loading a new file)
    $effect(() => {
        if (instance && !viewer) {
             // Update preview style if changed
             if (previewStyle) {
                 instance.changePreviewStyle(previewStyle);
             }
        }
    });

    $effect(() => {
        if (instance && !viewer && value !== instance.getMarkdown()) {
            // Only update if the content is significantly different
            // This is tricky. For now, we rely on the parent using {#key} to remount
            // when switching files.
        }
    });
</script>

<div bind:this={editorDiv} class="tui-editor-container"></div>

<style>
    .tui-editor-container {
        width: 100%;
        height: 100%;
        background: white; /* TUI Editor needs white bg by default */
        border-radius: 4px;
    }
    
    /* Global overrides for TUI Editor to match our theme if needed */
    :global(.toastui-editor-defaultUI) {
        border: none !important;
    }
</style>
