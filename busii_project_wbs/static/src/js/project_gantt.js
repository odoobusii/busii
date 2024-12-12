/** @odoo-module **/
import { GanttRenderer } from "@web_gantt/gantt_renderer";
import { patch } from "@web/core/utils/patch";
import { useState } from "@odoo/owl";

console.log("Custom Gantt Renderer: Initializing patch");

// Apply the patch to extend the GanttRenderer
patch(GanttRenderer.prototype, {
    
    // Add custom state management for dependencies, scales, etc.
    setup() {
        
        this.state = useState({
            canCreate: true,
            canEdit: true,
            dependencyEnabled: true,
            scales: ['day', 'week', 'month'], // Custom time scales
            
        });
        this.$draggedPill = null;
        console.log("Custom GanttRenderer initialized with state.");
        // this.setup(...arguments);
        super.setup();
    },

    /**
     * Custom method for getting stroke colors of tasks.
     */
    _getStrokeColors() {
        console.log("Getting stroke color for active tasks");
        // Custom color logic based on task state (e.g., active, overdue)
        return this._getStrokeAndHoveredStrokeColor(0, 128, 0);  // Green for active tasks
    },

    /**
     * Custom method for getting stroke color for overdue tasks.
     */
    _getStrokeErrorColors() {
        console.log("Getting stroke error color for overdue tasks");
        return this._getStrokeAndHoveredStrokeColor(211, 65, 59);  // Red for overdue tasks
    },

    /**
     * Trigger highlighting for pills when mouse enters
     * This is useful for displaying task dependencies or state.
     */
    async _onPillMouseEnter(ev) {
        console.log("Pill mouse enter:", ev);
        ev.stopPropagation();
        this._triggerPillHighlighting(ev.currentTarget, true);
    },

    /**
     * Trigger removing of pill highlighting when mouse leaves
     */
    async _onPillMouseLeave(ev) {
        console.log("Pill mouse leave:", ev);
        ev.stopPropagation();
        this._triggerPillHighlighting(ev.currentTarget, false);
    },

    /**
     * Custom method to highlight or remove highlight from task pills.
     * This is used to provide visual feedback.
     */
    _triggerPillHighlighting(pill, highlight) {
        console.log(`Highlighting pill: ${pill}, Highlight: ${highlight}`);
        if (highlight) {
            pill.classList.add('highlight');
        } else {
            pill.classList.remove('highlight');
        }
    },

    /**
     * Handler when a task pill is dragged.
     */
    _onStartDragging(event) {
        console.log("Started dragging task:", event);
        this.$draggedPill = event.data.$draggedPill;
        this.$draggedPill.addClass('o_dragged_pill');
        this.el.addClass('o_grabbing');
    },

    /**
     * Stop dragging a task pill.
     */
    _onStopDragging() {
        console.log("Stopped dragging task");
        this.$draggedPill.removeClass('o_dragged_pill');
        this.el.removeClass('o_grabbing');
    },

    /**
     * Custom handler for connector creation.
     * When a task is connected to another, update the dependencies.
     */
    async _onConnectorCreationDone(payload) {
        console.log("Connector creation done:", payload);
        this._connectorInCreation = null;
        const sourceId = parseInt(payload.data.sourceElement.dataset.id);
        const targetId = parseInt(payload.data.targetElement.dataset.id);
        
        // Trigger the creation of a connector (dependency between tasks)
        console.log(`Creating connector between tasks ${sourceId} and ${targetId}`);
        this.trigger_up('on_create_connector', {
            sourceId: sourceId,
            targetId: targetId,
            type: 'finish-to-start',  // Example dependency type
        });

        // Provide visual feedback for the connector
        this._togglePopoverVisibility(true);
    },

    /**
     * Handle mouse over event for connector highlighting.
     */
    _onConnectorMouseOver(payload) {
        console.log("Connector mouse over:", payload);
        this._triggerConnectorHighlighting(payload, true);
    },

    /**
     * Handle mouse out event for removing connector highlighting.
     */
    _onConnectorMouseOut(payload) {
        console.log("Connector mouse out:", payload);
        this._triggerConnectorHighlighting(payload, false);
    },

    /**
     * Helper function to trigger connector highlighting (on mouse over/out).
     */
    _triggerConnectorHighlighting(payload, highlight) {
        console.log(`Highlighting connector: ${highlight}`);
        const connector = payload.data.connectorElement;
        if (highlight) {
            connector.classList.add('highlight');
        } else {
            connector.classList.remove('highlight');
        }
    },

    /**
     * Toggle visibility of the popover UI element (used for feedback on actions).
     */
    _togglePopoverVisibility(visible) {
        console.log(`Popover visibility set to: ${visible}`);
        const popover = this.el.querySelector('.popover');
        if (popover) {
            if (visible) {
                popover.classList.add('visible');
            } else {
                popover.classList.remove('visible');
            }
        }
    },

    /**
     * Helper function to fetch the pills info (e.g., tasks) for rendering.
     */
    _getPillsInfo(row) {
        console.log(`Getting pills info for row: ${JSON.stringify(row)}`);
        return { pillData: row.pillData };
    },

    /**
     * Handle task creation from the UI.
     */
    _onTaskCreate(taskData) {
        console.log('Creating new task:', taskData);
        // Logic to trigger task creation in the backend (e.g., via RPC)
    }
});

// Now, you can use this patch to extend the existing GanttRenderer component
