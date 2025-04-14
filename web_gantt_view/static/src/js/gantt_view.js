odoo.define('web_gantt_view.GanttView', function (require) {
"use strict";

var core = require('web.core');
var AbstractView = require('web.AbstractView');
var view_registry = require('web.view_registry');
var GanttModel = require('web_gantt_view.GanttModel');
var GanttRenderer = require('web_gantt_view.GanttRenderer');
var Controller = require('web_gantt_view.GanttController');
var _lt = core._lt;

var GanttView = AbstractView.extend({
    display_name: _lt('Gantt'),
    icon: 'fa-tasks',
    config: _.extend({}, AbstractView.prototype.config, {
        Model: GanttModel,
        Controller: Controller,
        Renderer: GanttRenderer,
    }),
    viewType: 'gantt',

    init: function (viewInfo, params) {
        this._super.apply(this, arguments);
        var arch = this.arch;
        var fields = this.fields;
        var mapping = {name: 'name'};
        this.loadParams.arch = arch;
        this.loadParams.fields = fields;
        this.loadParams.mapping = mapping;
    },

});

view_registry.add('gantt', GanttView);

return GanttView;

});