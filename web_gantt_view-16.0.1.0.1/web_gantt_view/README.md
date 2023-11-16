# Instructions for Adding Gantt view

You can add Gnatt view with following syntax (Which is default odoo format)

<record id="view_your_model_gantt" model="ir.ui.view">
    <field name="name">model.name.gantt</field>
    <field name="model">model.name</field>
    <field name="type">gantt</field>
    <field name="arch" type="xml">
        <gantt date_start="date_start" date_stop="date" progress="progress_rate" string="Projects">
        </gantt>
    </field>
</record>


in action of related model where you want to add gantt view add gantt mode.

eg.
<record id="action_id" model="ir.actions.act_window">
    ......
    <field name="view_mode">kanban,tree,form,gantt</field>
    ......
</record>

