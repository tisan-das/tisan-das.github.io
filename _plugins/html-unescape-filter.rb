# frozen_string_literal: true
#
# `html_unescape`: turns the entities strip_html leaves behind (&gt;, &amp;,
# &#39;...) back into characters. The feed uses it on post summaries before
# escaping them for XML, so a reader shows `a > b`, not `a &gt; b`.

require 'cgi'

module HtmlUnescapeFilter
  def html_unescape(input)
    CGI.unescapeHTML(input.to_s)
  end
end

Liquid::Template.register_filter(HtmlUnescapeFilter)
