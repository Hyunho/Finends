class StrategyCatalog
  PROJECT_ROOT = Rails.root.join("..", "..").expand_path.freeze
  STRATEGIES_ROOT = PROJECT_ROOT.join("chilmyeonjo", "strategies").freeze

  Strategy = Struct.new(
    :name,
    :path,
    :documents,
    :history_documents,
    :source_files,
    :test_files,
    :summary,
    :updated_at,
    keyword_init: true
  )

  Document = Struct.new(
    :title,
    :slug,
    :relative_path,
    :repo_relative_path,
    :category,
    :path,
    :updated_at,
    :body,
    keyword_init: true
  ) do
    def history?
      category == :history
    end
  end

  def strategies
    return [] unless STRATEGIES_ROOT.directory?

    strategy_paths.map { |path| build_strategy(path) }.sort_by(&:name)
  end

  def fetch_strategy(name)
    path = strategy_directory_for(name)
    return unless path&.directory?

    build_strategy(path)
  end

  def fetch_document(strategy_name, doc_path)
    strategy = fetch_strategy(strategy_name)
    return unless strategy

    normalized = normalize_doc_path(doc_path)
    return if normalized.blank?

    (strategy.documents + strategy.history_documents).find { |document| document.slug == normalized }
  end

  private

  def strategy_paths
    STRATEGIES_ROOT.children.select(&:directory?).reject do |path|
      basename = path.basename.to_s
      basename.start_with?(".", "__")
    end
  end

  def strategy_directory_for(name)
    return unless safe_name?(name)

    STRATEGIES_ROOT.join(name)
  end

  def build_strategy(path)
    markdown_documents = build_documents(path)
    documents = markdown_documents.reject(&:history?)
    history_documents = markdown_documents.select(&:history?)
    source_files = relative_files(path.join("src"), path)
    test_files = relative_files(path.join("tests"), path)
    primary_document = documents.find { |document| document.slug.include?("strategy") } || documents.first

    Strategy.new(
      name: path.basename.to_s,
      path: path,
      documents: documents,
      history_documents: history_documents,
      source_files: source_files,
      test_files: test_files,
      summary: extract_summary(primary_document),
      updated_at: latest_timestamp(path, markdown_documents, source_files, test_files)
    )
  end

  def build_documents(strategy_path)
    Dir.glob(strategy_path.join("**", "*.md")).sort.filter_map do |filename|
      path = Pathname(filename)
      relative_path = path.relative_path_from(strategy_path).to_s
      next if relative_path.start_with?(".")

      slug = relative_path.delete_suffix(".md")
      title = extract_title(path) || humanize_filename(relative_path)
      category = relative_path.start_with?("history/") ? :history : :document

      Document.new(
        title: title,
        slug: slug,
        relative_path: relative_path,
        repo_relative_path: path.relative_path_from(PROJECT_ROOT).to_s,
        category: category,
        path: path,
        updated_at: path.mtime,
        body: path.read
      )
    end
  end

  def extract_title(path)
    path.read.each_line do |line|
      next unless line.start_with?("# ")

      return line.delete_prefix("# ").strip
    end

    nil
  end

  def humanize_filename(relative_path)
    File.basename(relative_path, ".md").tr("-", " ").split.map(&:capitalize).join(" ")
  end

  def extract_summary(primary_document)
    return "문서가 아직 없습니다." unless primary_document

    primary_document.body.each_line do |line|
      candidate = line.strip
      next if candidate.empty?
      next if candidate.start_with?("#", ">", "-", "*", "`")

      return candidate
    end

    "전략 문서가 준비되어 있습니다."
  end

  def latest_timestamp(strategy_path, documents, source_files, test_files)
    timestamps = documents.map(&:updated_at)
    timestamps.concat(source_files.map { |relative_path| strategy_path.join(relative_path).mtime })
    timestamps.concat(test_files.map { |relative_path| strategy_path.join(relative_path).mtime })
    timestamps.compact.max
  end

  def relative_files(base_path, strategy_path)
    return [] unless base_path.directory?

    Dir.glob(base_path.join("**", "*")).sort.filter_map do |filename|
      path = Pathname(filename)
      next if path.directory?

      path.relative_path_from(strategy_path).to_s
    end
  end

  def normalize_doc_path(doc_path)
    value = doc_path.to_s.delete_prefix("/").delete_suffix(".md")
    return if value.blank?
    return if value.include?("..")

    value
  end

  def safe_name?(value)
    value.to_s.match?(/\A[a-z0-9_]+\z/)
  end
end
