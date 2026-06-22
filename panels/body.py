import database as db
from panels.base import FormPanel

class BodyPanel(FormPanel):
    def _build_form(self):
        self._add_field("体重(kg)", "weight", is_text=False)
        self._add_field("体脂率  (%)", "body_fat", is_text=False)
        self._add_field("胸围(cm)", "chest", is_text=False)
        self._add_field("腰围(cm)", "waist", is_text=False)
        self._add_field("臂围(cm)", "arm", is_text=False)
        self._add_date_field()
        self._add_notes_field()
        self._add_save_button(self._save)

    def _save(self):
        try:
            db.add_body(
                weight=float(self._input_refs["weight"].text or 0) or None,
                body_fat=float(self._input_refs["body_fat"].text or 0) or None,
                chest=float(self._input_refs["chest"].text or 0) or None,
                waist=float(self._input_refs["waist"].text or 0) or None,
                arm=float(self._input_refs["arm"].text or 0) or None,
                record_date=self._input_date.text.strip(),
                notes=self._input_notes.text.strip())
            self._clear_inputs(["weight","body_fat","chest","waist","arm"])
            self._refresh_list()
            self.main_layout.refresh_heatmap()
        except (ValueError, Exception) as e:
            self._show_error(str(e))

    def _do_refresh_list(self):
        self.record_list.clear_widgets()
        target = self._view_date.isoformat()
        for r in db.get_body_records():
            if r["record_date"] != target: continue
            parts = [r["record_date"]]
            if r["weight"]: parts.append(f"{r['weight']}kg")
            if r["body_fat"]: parts.append(f" 体脂{r['body_fat']}%")
            if r["chest"]: parts.append(f" 胸{r['chest']}cm")
            if r["waist"]: parts.append(f" 腰{r['waist']}cm")
            if r["arm"]: parts.append(f" 臂{r['arm']}cm")
            self.record_list.add_widget(self._make_record_row("  ".join(parts), r["id"], self._delete))

    def _delete(self, rid):
        db.delete_body(rid)
        self._refresh_list()
        self.main_layout.refresh_heatmap()
