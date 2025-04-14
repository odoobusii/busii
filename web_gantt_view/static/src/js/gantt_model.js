odoo.define('web_gantt_view.GanttModel', function (require) {
"use strict";

var AbstractModel = require('web.AbstractModel');
var concurrency = require('web.concurrency');
var time = require('web.time');
var field_utils = require('web.field_utils');

var core = require('web.core');
var _t = core._t;


return AbstractModel.extend({

    init: function () {
        this._super.apply(this, arguments);
        this.data = null;
        this.dp = new concurrency.DropPrevious();
    },

    get: function () {
        return _.extend({}, this.data);
    },

    load: function (params) {
        this.modelName = params.modelName;
        this.data = {
            records: [],
            domain: params.domain,
            context: params.context,
            groupedBy: params.groupedBy || [],
            arch: params.arch.attrs,
            mapping: params.mapping,
            fields: params.fields,
        };

        return this._loadData().then(function () {
            return Promise.resolve();
        });

    },

    reload: function (handle, params) {
        if (params.domain) {
            this.data.domain = params.domain;
        }
        if (params.context) {
            this.data.context = params.context;
        }
        if (params.groupBy) {
            this.data.groupedBy = params.groupBy;
        }
        return this._loadData();
    },

    _loadData: function () {
        var self = this;

        var dataDef = this._rpc({
            route: '/web/dataset/search_read',
            model: this.modelName,
            context: this.data.context,
            domain: this.data.domain,
        });

        return this.dp.add(Promise.all([dataDef])).then(function (results) {
            self.data.records = self._ProcessData(results[0].records);
            return self
        });
    },

    _ProcessData: function (raw_datas) {
        var self = this;
        var ganttData = [];
        var group_bys = self.data.groupedBy;
        var tasks = raw_datas;
        //prevent more that 1 group by
        //if (group_bys.length > 0) {
        //   group_bys = [group_bys[0]];
        //}

        // if there is no group by
        if (group_bys.length == 0) {
            group_bys = ["_pseudo_group_by"];
        }

        // get the groups
        var split_groups = function(tasks, group_bys) {
            if (group_bys.length === 0)
                return tasks;
            var groups = [];
            _.each(tasks, function(task) {
                var group_name = task[_.first(group_bys)];
                var group = _.find(groups, function(group) { return _.isEqual(group.name, group_name); });
                if (group === undefined) {
                    group = {name:group_name, tasks: [], __is_group: true};
                    groups.push(group);
                }
                group.tasks.push(task);
            });
            _.each(groups, function(group) {
                group.tasks = split_groups(group.tasks, _.rest(group_bys));
            });
            return groups;
        }
        var groups = split_groups(tasks, group_bys);
        
        // track ids of task items for context menu
        var task_ids = {};
        // creation of the chart
        var generate_task_info = function(task, plevel) {
            if (_.isNumber(task[self.data.arch['progress']])) {
                var percent = task[self.data.arch['progress']] || 0;
            } else {
                var percent = 100;
            }
            var level = plevel || 0;
            if (task.__is_group) {
                var task_infos = _.compact(_.map(task.tasks, function(sub_task) {
                    return generate_task_info(sub_task, level + 1);
                }));
                if (task_infos.length == 0)
                    return;
                var task_start = _.reduce(_.pluck(task_infos, "task_start"), function(date, memo) {
                    return memo === undefined || date < memo ? date : memo;
                }, undefined);
                var task_stop = _.reduce(_.pluck(task_infos, "task_stop"), function(date, memo) {
                    return memo === undefined || date > memo ? date : memo;
                }, undefined);
                var duration = (task_stop.getTime() - task_start.getTime()) / (1000 * 60 * 60);
                //covert in business hours.
                duration = (duration / 24) * 8;
                var group_name = ' - ';
                if (group_bys[level] != '_pseudo_group_by') {
                    if (task['name'] && task['name'].constructor == Array) {
                        group_name = task['name'][1];
                    } else {
                        group_name = task['name'];
                    }
                }
                if (level == 0) {
                    var group = new GanttProjectInfo(_.uniqueId("gantt_project_"), group_name, task_start);
                    _.each(task_infos, function(el) {
                        group.addTask(el.task_info);
                    });
                    return group;
                } else {
                    var group = new GanttTaskInfo(_.uniqueId("gantt_project_task_"), group_name, task_start, duration || 1, percent);
                    _.each(task_infos, function(el) {
                        group.addChildTask(el.task_info);
                    });
                    return {task_info: group, task_start: task_start, task_stop: task_stop};
                }
            } else {
                var task_name = task['name'];
                var duration_in_business_hours = false;
                var task_start = time.auto_str_to_date(task[self.data.arch['date_start']]);
                if (!task_start)
                    return;
                var task_stop;
                if (task[self.data.arch['date_stop']]) {
                    task_stop = time.auto_str_to_date(task[self.data.arch['date_stop']]);
                    if (!task_stop)
                        task_stop = task_start;
                } else { 
                    return;
                }
                var duration = (task_stop.getTime() - task_start.getTime()) / (1000 * 60 * 60);
                var id = _.uniqueId("gantt_task_");
                if (!duration_in_business_hours){
                    duration = (duration / 24) * 8;
                }
                var task_info = new GanttTaskInfo(id, task_name, task_start, (duration) || 1, percent);
                task_info.internal_task = task;
                task_ids[id] = task_info;
                return {task_info: task_info, task_start: task_start, task_stop: task_stop};
            }
        }

        _.each(_.compact(_.map(groups, function(e) {return generate_task_info(e, 0);})), function(project) {
            ganttData.push(project);
        });
        return ganttData;
    },

});

});