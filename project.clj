(defproject metabase-gizmosql-driver "1.0.0-SNAPSHOT"
  :description "A Metabase driver for GizmoSQL — an Arrow Flight SQL server backed by DuckDB — using the GizmoSQL JDBC driver."
  :url "https://github.com/gizmodata/metabase-gizmosql-driver"
  :license {:name "Apache-2.0"
            :url "https://www.apache.org/licenses/LICENSE-2.0"}
  :dependencies [[org.clojure/clojure "1.11.1"]
                 [com.gizmodata/gizmosql-jdbc-driver "1.7.0"]]
  :repl-options {:init-ns metabase.driver.gizmosql})
