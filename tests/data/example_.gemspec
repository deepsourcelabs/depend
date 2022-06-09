# -*- ruby -*-

require 'rubygems'
require 'hoe'

Hoe.plugin :git
Hoe.plugin :bundler

Hoe.spec 'hoe-gemspec' do
  developer('Mike Dalessio', 'mike.dalessio@gmail.com')
  license "MIT"

  self.history_file     = "CHANGELOG.md"
  self.readme_file      = "README.md"
  self.test_globs       = ["test/test_*.rb"]

  extra_dev_deps << ["minitest", "~> 5.11"]
  extra_dev_deps << ["hoe-git", ">=0"]
  extra_dev_deps << ["hoe-bundler", ">=0"]
  extra_dev_deps << ["concourse", "~> 0.23"]
end

require "concourse"

Concourse.new("hoe-gemspec", fly_target: "flavorjones").create_tasks!