odoo.define('web_gantt_view.GanttRenderer', function (require) {
"use strict";

var core = require('web.core');
var AbstractRenderer = require('web.AbstractRenderer');
var Dialog = require('web.Dialog');
var time = require('web.time');

var _t = core._t;
var QWeb = core.qweb;

return AbstractRenderer.extend({
    template: "GanttView",

    init: function (parent, state, params) {
        this.parent = parent;
        this._super.apply(this, arguments);
        this.chart_id = _.uniqueId();
    },

    _render: function () {
        this.data = this.state;
        if (this.data.records == 0) {
            this.$el.empty();
            this.$el.append(_t('<div class="oe_view_nocontent"><p class="oe_view_nocontent_create">Click to add a new record.</p></div>'));
        } else {
            this._LoadGanttView();
        }
        return $.when();
    },
    
    _LoadGanttView: function () {
        var self = this;
        this.$el.find(".acs_gantt").empty();
        var $div = $("<div class='acs_chart_body' id='" + this.chart_id + "'></div>");
        $div.css('min-height', 500);
        $div.prependTo(document.body);
        var gantt = new GanttChart();

        _.each(self.data.records, function(project) {
            gantt.addProject(project);
        });
        gantt.setEditable(true);
        gantt.setImagePath("/web_gantt_view/static/lib/dhtmlxGantt/codebase/imgs/");
        gantt.attachEvent("onTaskEndDrag", function(task) {
            self.on_task_changed(task);
        });
        gantt.attachEvent("onTaskEndResize", function(task) {
            self.on_task_changed(task);
        });
        gantt.attachEvent("onTaskClick", function(task) {
            self.on_task_display(task);
        });
        gantt.create(this.chart_id);
        this.$el.children().append($div.contents());
        $div.remove();
    },

    on_task_display: function(task) {
        if (!task.wasMoved){
            this.trigger_up('openRecord', task.TaskInfo.internal_task);
        }
    },

    on_task_create: function() {
        this.trigger_up('createRecord');
    },

    on_task_changed: function(task_obj) {
        var self = this;
        var itask = task_obj.TaskInfo.internal_task;
        var start = task_obj.getEST();
        var duration = task_obj.getDuration();
        /*var duration_in_business_hours = !!self.fields_view.arch.attrs.date_delay;
        if (!duration_in_business_hours){
            duration = (duration / 8 ) * 24;
        }*/
        duration = (duration / 8 ) * 24;
        var end = new Date(start);
        end.setMilliseconds(duration * 60 * 60 * 1000);
        var data = {};
        data['id'] = itask.id;
        data[self.arch.attrs.date_start] = time.auto_date_to_str(start, 'datetime');
        if (self.arch.attrs.date_stop) {
            data[self.arch.attrs.date_stop] = 
                time.auto_date_to_str(end, 'datetime');
        } else {
            data[self.arch.attrs.date_delay] = duration;
        }
        self.trigger_up('updateRecord', data);
    },

});

});
