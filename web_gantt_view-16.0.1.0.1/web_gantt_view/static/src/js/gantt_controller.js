/** @odoo-module alias=web_gantt_view.GanttController */

import AbstractController from 'web.AbstractController';
import core from 'web.core';
import config from 'web.config';
import { confirm as confirmDialog } from 'web.Dialog';
import { Domain } from '@web/core/domain';
import { FormViewDialog } from "@web/views/view_dialogs/form_view_dialog";
import { SelectCreateDialog } from "@web/views/view_dialogs/select_create_dialog";

const QWeb = core.qweb;
const _t = core._t;
const { Component } = owl;

export default AbstractController.extend({
    
    custom_events: _.extend({}, AbstractController.prototype.custom_events, {
        updateRecord: '_onUpdateRecord',
        openRecord: '_openRecord',
    }),

    init(parent, model, renderer, params) {
        this._super.apply(this, arguments);
        this.set('title', this.displayName);
        this.context = params.context;
    },

    renderButtons($node) {
        this.$buttons = $(QWeb.render("GanttViewCreateButton", {widget: this}));
        this.$buttons.on('click', '.acs_gantt_button_create', this._createaRecord.bind(this));
        this.$buttons.appendTo($node);
    },

    _onUpdateRecord(record) {
        this._rpc({
            model: this.model.modelName,
            method: 'write',
            args: [record.data.id, {
                [this.model.data.arch['date_start']]: record.data[this.model.data.arch['date_start']],
                [this.model.data.arch['date_stop']]: record.data[this.model.data.arch['date_stop']],
            }],
        }).then(this.reload.bind(this));
    },

    _openRecord(record) {
        Component.env.services.dialog.add(FormViewDialog, {
            title: _t("Open"),
            resModel: this.model.modelName,
            //viewId: this.dialogViews[0][0],
            resId: record.data.id,
        });
    },

    _createaRecord() {
        Component.env.services.dialog.add(FormViewDialog, {
            title: _t("Create"),
            resModel: this.model.modelName,
        });
    },

});