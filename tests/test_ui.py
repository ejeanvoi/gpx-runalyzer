from __future__ import annotations

from src.analysis.splits import SPLIT_DISTANCES
from src.ui.comparison_view import _short_name, _similarity_label
from src.ui.formatting import format_distance_km
from src.ui.widgets.activity_list import ActivityListModel, ActivityListView
from src.ui.widgets.elevation_chart import SeriesChart
from src.ui.widgets.filters import FiltersWidget


class TestFiltersWidget:
    def test_can_create(self, qtbot):
        w = FiltersWidget(["running", "trail_running"])
        qtbot.add_widget(w)
        w.show()
        assert w.isVisible()

    def test_sets_activity_types(self, qtbot):
        w = FiltersWidget()
        qtbot.add_widget(w)
        w.set_activity_types(["running", "cycling"])
        combo = w._combo_type
        assert combo.count() == 3

    def test_apply_emits_filters(self, qtbot):
        w = FiltersWidget(["running", "cycling"])
        qtbot.add_widget(w)
        received: list = []
        w.filters_changed.connect(received.append)
        w._btn_apply.click()
        assert len(received) == 1
        filters = received[0]
        assert "activity_types" in filters
        assert "start_date" in filters
        assert "end_date" in filters
        assert len(filters["activity_types"]) == 2


class TestSeriesChart:
    def test_can_create(self, qtbot):
        w = SeriesChart()
        qtbot.add_widget(w)
        w.show()
        assert w.isVisible()

    def test_checkbox_state(self, qtbot):
        w = SeriesChart()
        assert w._curves["Pace"]["visible"]
        assert not w._curves["Elevation"]["visible"]

    def test_set_activity_no_crash(self, qtbot, sample_activity):
        w = SeriesChart()
        qtbot.add_widget(w)
        w.set_activity(sample_activity)
        for name in ("Pace", "Elevation", "Heart Rate", "Vertical Speed"):
            assert len(w._curves[name]["data"]) == len(sample_activity.points)


class TestActivityList:
    def test_can_create(self, qtbot):
        w = ActivityListView()
        qtbot.add_widget(w)
        w.show()
        assert w.isVisible()

    def test_model_empty(self, qtbot):
        model = ActivityListModel()
        assert model.rowCount() == 0

    def test_model_populated(self, qtbot, store):
        model = ActivityListModel()
        acts = store.get_all()
        metrics_map = {a.id: store.get_metrics(a) for a in acts}
        model.set_activities(acts, metrics_map)
        assert model.rowCount() == len(acts)

    def test_activity_at_returns_activity(self, qtbot, store):
        model = ActivityListModel()
        acts = store.get_all()
        metrics_map = {a.id: store.get_metrics(a) for a in acts}
        model.set_activities(acts, metrics_map)
        act = model.activity_at(0)
        assert act is not None
        assert act is acts[0]

    def test_activity_at_out_of_range(self, qtbot, store):
        model = ActivityListModel()
        acts = store.get_all()
        metrics_map = {a.id: store.get_metrics(a) for a in acts}
        model.set_activities(acts, metrics_map)
        assert model.activity_at(-1) is None
        assert model.activity_at(99) is None


class TestDashboardView:
    def test_can_create(self, qtbot, store):
        from src.ui.dashboard import DashboardView
        view = DashboardView(store)
        qtbot.add_widget(view)
        view.show()
        assert view.isVisible()

    def test_summary_shows_count(self, qtbot, store):
        from src.ui.dashboard import DashboardView
        view = DashboardView(store)
        qtbot.add_widget(view)
        acts = store.get_all()
        filters = {
            "activity_types": set(store.activity_types),
            "start_date": None,
            "end_date": None,
        }
        view._filters.filters_changed.emit(filters)
        qtbot.wait(10)
        text = view._summary_labels[0].text()
        assert str(len(acts)) in text

    def test_summary_shows_distance(self, qtbot, store):
        from src.ui.dashboard import DashboardView
        view = DashboardView(store)
        qtbot.add_widget(view)
        filters = {
            "activity_types": set(store.activity_types),
            "start_date": None,
            "end_date": None,
        }
        view._filters.filters_changed.emit(filters)
        qtbot.wait(10)
        text = view._summary_labels[1].text()
        assert "Distance:" in text
        assert "." in text

    def test_filter_by_type(self, qtbot, store):
        from src.ui.dashboard import DashboardView
        view = DashboardView(store)
        qtbot.add_widget(view)
        view._filters._combo_type.setCurrentText("running")
        view._filters._btn_apply.click()
        qtbot.wait(10)
        model = view._list_model
        for i in range(model.rowCount()):
            act = model.activity_at(i)
            assert act.activity_type == "running"

    def test_empty_store_shows_zeros(self, qtbot):
        from pathlib import Path

        from src.services.store import ActivityStore
        from src.ui.dashboard import DashboardView
        empty_store = ActivityStore(Path("/nonexistent"))
        empty_store.load()
        view = DashboardView(empty_store)
        qtbot.add_widget(view)
        filters = {
            "activity_types": set(),
            "start_date": None,
            "end_date": None,
        }
        view._on_filters_changed(filters)
        assert "0" in view._summary_labels[0].text()
        assert "--:--" in view._summary_labels[3].text()

    def test_pr_labels_created(self, qtbot, store):
        from src.ui.dashboard import DashboardView
        view = DashboardView(store)
        qtbot.add_widget(view)
        assert len(view._pr_labels) == 5

    def test_pr_populated_on_filter(self, qtbot, store):
        from src.ui.dashboard import DashboardView
        view = DashboardView(store)
        qtbot.add_widget(view)
        filters = {
            "activity_types": set(store.activity_types),
            "start_date": None,
            "end_date": None,
        }
        view._filters.filters_changed.emit(filters)
        qtbot.wait(10)
        for pr_lbl in view._pr_labels:
            assert ":" in pr_lbl.text()

    def test_activity_click_emits_signal(self, qtbot, store):
        from src.ui.dashboard import DashboardView
        view = DashboardView(store)
        qtbot.add_widget(view)
        received: list = []
        view.activity_selected.connect(received.append)
        acts = store.get_all()
        filters = {
            "activity_types": set(store.activity_types),
            "start_date": None,
            "end_date": None,
        }
        view._filters.filters_changed.emit(filters)
        qtbot.wait(10)
        view._list_view.activity_clicked.emit(acts[0])
        assert len(received) == 1
        assert received[0] is acts[0]


class TestActivityDetailView:
    def test_can_create(self, qtbot, store):
        from src.ui.activity_detail import ActivityDetailView
        view = ActivityDetailView(store)
        qtbot.add_widget(view)
        view.show()
        assert view.isVisible()

    def test_set_activity_populates_header(self, qtbot, store_with_activity):
        from src.ui.activity_detail import ActivityDetailView
        store, act = store_with_activity
        view = ActivityDetailView(store)
        qtbot.add_widget(view)
        view.set_activity(act)
        header_text = view._header_label.text()
        assert act.name in header_text

    def test_set_activity_populates_distance(self, qtbot, store_with_activity):
        from src.ui.activity_detail import ActivityDetailView
        store, act = store_with_activity
        view = ActivityDetailView(store)
        qtbot.add_widget(view)
        m = store.get_metrics(act)
        view.set_activity(act)
        expected = format_distance_km(m["distance_km"])
        assert expected in view._card_distance.text()

    def test_set_activity_populates_pace(self, qtbot, store_with_activity):
        from src.ui.activity_detail import ActivityDetailView
        store, act = store_with_activity
        view = ActivityDetailView(store)
        qtbot.add_widget(view)
        view.set_activity(act)
        assert view._card_pace.text() != "--"

    def test_set_activity_populates_elevation(self, qtbot, store_with_activity):
        from src.ui.activity_detail import ActivityDetailView
        store, act = store_with_activity
        view = ActivityDetailView(store)
        qtbot.add_widget(view)
        m = store.get_metrics(act)
        view.set_activity(act)
        text = view._card_elevation.text()
        assert f"{m['elevation_gain_m']:.0f}" in text

    def test_set_activity_populates_hr(self, qtbot, store_with_activity):
        from src.ui.activity_detail import ActivityDetailView
        store, act = store_with_activity
        view = ActivityDetailView(store)
        qtbot.add_widget(view)
        m = store.get_metrics(act)
        view.set_activity(act)
        avg_hr = m.get("avg_hr")
        if avg_hr:
            assert f"{avg_hr:.0f}" in view._card_hr.text()

    def test_type_badge_shows_emoji(self, qtbot, store_with_activity):
        from src.ui.activity_detail import ActivityDetailView
        store, act = store_with_activity
        view = ActivityDetailView(store)
        qtbot.add_widget(view)
        view.set_activity(act)
        badge_text = view._type_badge.text()
        assert len(badge_text) > 1

    def test_splits_labels_created(self, qtbot, store_with_activity):
        from src.ui.activity_detail import ActivityDetailView
        store, act = store_with_activity
        view = ActivityDetailView(store)
        qtbot.add_widget(view)
        view.set_activity(act)
        assert len(view._split_labels) == len(SPLIT_DISTANCES)

    def test_compare_button_emits_signal(self, qtbot, store_with_activity):
        from src.ui.activity_detail import ActivityDetailView
        store, act = store_with_activity
        view = ActivityDetailView(store)
        qtbot.add_widget(view)
        received: list = []
        view.compare_route_requested.connect(received.append)
        view.set_activity(act)
        view._btn_compare.click()
        assert len(received) == 1
        assert received[0] is act


class TestComparisonView:
    def test_can_create(self, qtbot, store):
        from src.ui.comparison_view import ComparisonView
        view = ComparisonView(store, store.get_all())
        qtbot.add_widget(view)
        view.show()
        assert view.isVisible()

    def test_set_reference_populates_table(self, qtbot, store_with_activity):
        from src.ui.comparison_view import ComparisonView
        store, act = store_with_activity
        view = ComparisonView(store, store.get_all())
        qtbot.add_widget(view)
        view._slider.setValue(10)
        view.set_reference(act)
        qtbot.wait(10)
        table = view._table
        assert table.rowCount() >= 1
        assert table.columnCount() == 8

    def test_table_first_row_is_reference(self, qtbot, store_with_activity):
        from src.ui.comparison_view import ComparisonView
        store, act = store_with_activity
        view = ComparisonView(store, store.get_all())
        qtbot.add_widget(view)
        view._slider.setValue(10)
        view.set_reference(act)
        qtbot.wait(10)
        first_name = view._table.item(0, 1)
        assert first_name is not None
        assert first_name.text() == act.name

    def test_row_double_click_emits_signal(self, qtbot, store_with_activity):
        from src.ui.comparison_view import ComparisonView
        store, act = store_with_activity
        view = ComparisonView(store, store.get_all())
        qtbot.add_widget(view)
        received: list = []
        view.go_to_activity.connect(received.append)
        view._slider.setValue(10)
        view.set_reference(act)
        qtbot.wait(10)
        item = view._table.item(0, 0)
        assert item is not None
        view._on_row_double_click(item)
        assert len(received) == 1

    def test_slider_updates_label(self, qtbot, store_with_activity):
        from src.ui.comparison_view import ComparisonView
        store, _act = store_with_activity
        view = ComparisonView(store, store.get_all())
        qtbot.add_widget(view)
        view._slider.setValue(75)
        qtbot.wait(5)
        assert view._threshold_label.text() == "75%"


class TestShortName:
    def test_short_name_no_truncation(self):
        assert _short_name("Morning") == "Morning"

    def test_short_name_exact_length(self):
        assert _short_name("1234567890") == "1234567890"

    def test_short_name_truncates(self):
        result = _short_name("Morning Run Long", 10)
        assert len(result) == 10
        assert result.endswith("\u2026")

    def test_short_name_empty(self):
        assert _short_name("") == ""

    def test_short_name_none(self):
        assert _short_name(None) == ""


class TestSimilarityLabel:
    def test_high_similarity(self):
        assert "🟢" in _similarity_label(0.95)

    def test_medium_similarity(self):
        assert "🟡" in _similarity_label(0.65)

    def test_low_similarity(self):
        assert "🟠" in _similarity_label(0.3)

    def test_exact_boundary_0_8(self):
        assert "🟢" in _similarity_label(0.8)

    def test_exact_boundary_0_5(self):
        assert "🟡" in _similarity_label(0.5)

    def test_zero_similarity(self):
        label = _similarity_label(0.0)
        assert "0%" in label
