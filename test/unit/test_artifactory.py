from testbase import TestBase
from servicemanager.smartifactory import SmArtifactory
from xml.dom.minidom import parseString

class TestArtifactory(TestBase):



    def test_should_find_latest_999_SNAPSHOT(self):
        context = self.createContext()
        artifactory = SmArtifactory(context, "PLAY_ARTIFACTORY_END_TO_END_TEST")


        maven_metadata=parseString("""<?xml version="1.0" encoding="UTF-8"?>
          <metadata modelVersion="1.1.0">
            <groupId>uk.gov.hmrc</groupId>
            <artifactId>auth_2.11</artifactId>
            <versioning>
              <latest>999-SNAPSHOT</latest>
              <release></release>
              <versions>
                <version>999-SNAPSHOT</version>
              </versions>
              <lastUpdated>20141216000306</lastUpdated>
            </versioning>
          </metadata>
          """)

        self.assertEqual(artifactory.find_latest_in_dom(maven_metadata), '999-SNAPSHOT')

    def test_should_find_latest_999_SNAPSHOT_with_no_releases(self):
        context = self.createContext()
        artifactory = SmArtifactory(context, "PLAY_ARTIFACTORY_END_TO_END_TEST")


        maven_metadata=parseString("""<?xml version="1.0" encoding="UTF-8"?>
          <metadata modelVersion="1.1.0">
            <groupId>uk.gov.hmrc</groupId>
            <artifactId>datastream_2.11</artifactId>
            <version>999-SNAPSHOT</version>
            <versioning>
              <latest>999-SNAPSHOT</latest>
              <versions>
                <version>999-SNAPSHOT</version>
              </versions>
              <lastUpdated>20180720112718</lastUpdated>
            </versioning>
          </metadata>
          """)

        self.assertEqual(artifactory.find_latest_in_dom(maven_metadata), '999-SNAPSHOT')

    def test_should_find_latest_git_describe_version(self):
        context = self.createContext()
        artifactory = SmArtifactory(context, "PLAY_ARTIFACTORY_END_TO_END_TEST")


        maven_metadata=parseString("""<?xml version="1.0" encoding="UTF-8"?>
          <metadata>
            <groupId>uk.gov.hmrc</groupId>
            <artifactId>leak-detection_2.11</artifactId>
            <version>0.59.0-2-ga922e3a</version>
            <versioning>
              <latest>0.59.0-2-ga922e3a</latest>
              <release>0.59.0-2-ga922e3a</release>
              <versions>
                <version>0.59.0-1-g1b18f61</version>
                <version>0.59.0-2-ga922e3a</version>
              </versions>
              <lastUpdated>20180706042728</lastUpdated>
            </versioning>
          </metadata>
          """)

        self.assertEqual(artifactory.find_latest_in_dom(maven_metadata), '0.59.0-2-ga922e3a')


    def test_should_find_latest_git_describe_version_with_999_SNAPSHOT_as_latest(self):
        context = self.createContext()
        artifactory = SmArtifactory(context, "PLAY_ARTIFACTORY_END_TO_END_TEST")


        maven_metadata=parseString("""<?xml version="1.0" encoding="UTF-8"?>
          <metadata modelVersion="1.1.0">
            <groupId>uk.gov.hmrc</groupId>
            <artifactId>pertax-frontend_2.11</artifactId>
            <versioning>
              <latest>999-SNAPSHOT</latest>
              <release>1.334.0-1-gbb6e76c</release>
              <versions>
                <version>1.334.0-1-gbb6e76c</version>
                <version>999-SNAPSHOT</version>
              </versions>
              <lastUpdated>20180720042029</lastUpdated>
            </versioning>
          </metadata>""")

        self.assertEqual(artifactory.find_latest_in_dom(maven_metadata), '1.334.0-1-gbb6e76c')

