class MarkdownRenderer
  def render(markdown)
    Kramdown::Document.new(
      markdown.to_s,
      input: "GFM",
      syntax_highlighter: nil,
      hard_wrap: false
    ).to_html
  end
end
