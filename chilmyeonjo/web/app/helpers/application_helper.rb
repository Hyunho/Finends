module ApplicationHelper
  def format_timestamp(time)
    return "n/a" unless time

    time.in_time_zone.strftime("%Y-%m-%d %H:%M")
  end

  def document_category_label(document)
    document.history? ? "History" : "Document"
  end

  def document_css_class(document)
    document.history? ? "pill history" : "pill"
  end

  def page_title(value = nil)
    base = "Finends Strategy Viewer"
    value.present? ? "#{value} | #{base}" : base
  end
end
